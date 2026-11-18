"""Tests locaux du service TTL-LAMa sans accès réseau ni base réelle."""

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from importlib import import_module
from types import ModuleType
from unittest.mock import MagicMock, call

import pytest
from flask import Flask, g
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from ttlama_sdk.errors import APIError
from werkzeug.exceptions import BadRequest

from app.models import User
from app.repositories.auth_session import create_auth_session
from app.ttlama import VPNSyncError, profiles_for_habilitation, sync_user


@pytest.mark.parametrize(
    ('habilitation', 'expected'),
    (
        (17, {1, 2}),
        (37, {2, 3}),
        (57, {2}),
        (67, set[int]()),
        (7, set[int]()),
    ),
)
def test_profiles_for_habilitation(habilitation: int, expected: set[int]) -> None:
    """Détermine les profils SDK à affecter depuis les droits Intranet."""
    assert profiles_for_habilitation(habilitation) == expected


def _vpn_user(database: Session) -> User:
    user = database.get(User, 1)
    assert user is not None
    return user


def _do_nothing(*_args: object, **_kwargs: object) -> None:
    return None


@contextmanager
def _test_database(
    monkeypatch: pytest.MonkeyPatch,
    database: Session | MagicMock,
) -> Generator[None, None, None]:
    with monkeypatch.context() as scoped_patch:
        scoped_patch.setattr(
            g._get_current_object(), 'db_session', database,  # pylint: disable=W0212
            raising=False,
        )
        yield


@pytest.fixture
def vpn_database() -> Iterator[Session]:
    """Fixture fournissant une base de données VPN factice."""
    engine = create_engine('sqlite://')
    User.__table__.create(engine)
    with Session(engine, expire_on_commit=False) as database:
        database.add(User(
            id=1, prenom='Alice', nom='Test', identifiant='alice',
            mail='alice@example.org', sha_mdp='secret-technique', habilitation=17,
            vpn_profiles=[1, 2], vpn_sync_state='pending', vpn_password_dirty=True,
        ))
        database.commit()
        yield database
    engine.dispose()


@pytest.fixture
def vpn_api(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Fixture fournissant un client VPN factice."""
    client = MagicMock()
    client.profile.list.return_value = [
        {'id': 1, 'name': 'Administrateur', 'revoked_at': None},
        {'id': 2, 'name': 'Fichiers Samba', 'revoked_at': None},
        {'id': 3, 'name': 'Charlemagne', 'revoked_at': None},
    ]
    client.user.create.return_value = {'id': '12345678-1234-4234-8234-123456789abc'}
    client.user.get.return_value = {'enabled': True}
    client.user.profiles.return_value = []

    @contextmanager
    def fake_client() -> Generator[MagicMock, None, None]:
        yield client

    monkeypatch.setattr('app.ttlama.admin_client', fake_client)
    return client


def test_creation_et_attribution(
    vpn_database: Session, vpn_api: MagicMock, # pylint: disable=W0621
) -> None:
    """Test de création et d'attribution d'un profil VPN."""
    sync_user(vpn_database, 1)
    user = _vpn_user(vpn_database)
    assert user.vpn_uuid == '12345678-1234-4234-8234-123456789abc'
    assert user.vpn_sync_state == 'synced'
    vpn_api.user.create.assert_called_once_with(
        'alice', email='alice@example.org', password='secret-technique'
    )
    vpn_api.user.assign_profile.assert_has_calls([
        call(user.vpn_uuid, 1),
        call(user.vpn_uuid, 2),
    ])


def test_creation_incertitude_exige_verification(
    vpn_database: Session, vpn_api: MagicMock, # pylint: disable=W0621
) -> None:
    """Test that if VPN user creation fails, the sync state is set to 'review' and raises
    VPNSyncError.
    """
    vpn_api.user.create.side_effect = APIError('timeout')
    with pytest.raises(VPNSyncError):
        sync_user(vpn_database, 1)
    assert _vpn_user(vpn_database).vpn_sync_state == 'review'
    with pytest.raises(VPNSyncError):
        sync_user(vpn_database, 1)
    assert vpn_api.user.create.call_count == 1


def test_retrait_desactive_compte(
    vpn_database: Session, vpn_api: MagicMock, # pylint: disable=W0621
) -> None:
    """Test de comportement à la mise à jour et désactivation de compte."""
    user = _vpn_user(vpn_database)
    user.vpn_uuid = '12345678-1234-4234-8234-123456789abc'
    user.habilitation = 1
    vpn_database.commit()
    sync_user(vpn_database, 1)
    vpn_api.user.delete.assert_called_once_with(user.vpn_uuid)
    assert user.vpn_sync_state == 'synced'


def test_reprise_met_a_jour_secret_et_profils(
    vpn_database: Session, vpn_api: MagicMock, # pylint: disable=W0621
) -> None:
    """Test that when a user's VPN account is already created, the password and profiles are
    updated correctly.
    """
    user = _vpn_user(vpn_database)
    user.vpn_uuid = '12345678-1234-4234-8234-123456789abc'
    vpn_api.user.profiles.return_value = [{'profile_id': 3, 'revoked_at': None}]
    vpn_database.commit()
    sync_user(vpn_database, 1)
    vpn_api.user.update.assert_called_once_with(
        user.vpn_uuid, username='alice', email='alice@example.org', password='secret-technique'
    )
    vpn_api.user.unassign_profile.assert_called_once_with(user.vpn_uuid, 3)
    vpn_api.user.assign_profile.assert_has_calls([
        call(user.vpn_uuid, 1),
        call(user.vpn_uuid, 2),
    ])
    assert not user.vpn_password_dirty


def test_reprise_met_a_jour_identifiant_et_mail(
    vpn_database: Session, vpn_api: MagicMock, # pylint: disable=W0621
) -> None:
    """Synchronise les changements d'identifiant et d'adresse mail."""
    user = _vpn_user(vpn_database)
    user.vpn_uuid = '12345678-1234-4234-8234-123456789abc'
    user.vpn_password_dirty = False
    vpn_api.user.get.return_value = {
        'enabled': True,
        'username': 'ancien-identifiant',
        'email': 'ancien@example.org',
    }
    vpn_api.user.profiles.return_value = [{'profile_id': 1, 'revoked_at': None}]
    user.identifiant = 'alice-nouveau'
    user.mail = 'alice-nouveau@example.org'
    vpn_database.commit()

    sync_user(vpn_database, 1)

    vpn_api.user.update.assert_called_once_with(
        user.vpn_uuid,
        username='alice-nouveau',
        email='alice-nouveau@example.org',
    )
    assert user.vpn_sync_state == 'synced'


@pytest.fixture
def rights_application(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Charge les routes sans initialiser de base ou de service externe."""
    monkeypatch.setattr('app.config.database.initialize_database', _do_nothing)
    monkeypatch.setattr('app.rapport_echeances.validate_report_configuration', _do_nothing)
    return import_module('app.application')


def test_route_vpn_profiles_utilise_les_profils_sdk(
    vpn_database: Session, # pylint: disable=W0621
    vpn_api: MagicMock, # pylint: disable=W0621
    rights_application: ModuleType, # pylint: disable=W0621
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La route délivre les profils SDK correspondant aux habilitations courantes."""
    import app.ttlama as vpn_service # pylint: disable=C0415

    monkeypatch.setattr(rights_application, 'admin_client', vpn_service.admin_client)
    with rights_application.peraudiere.test_request_context(
        '/gestion-droits/1/vpn-profils?habilitation=37'
    ):
        with _test_database(monkeypatch, vpn_database):
            response = rights_application.vpn_profiles.__wrapped__(1)

    assert response.status_code == 200
    assert response.get_json() == {
        'pending': True,
        'profiles': [
            {'id': 2, 'name': 'Fichiers Samba'},
            {'id': 3, 'name': 'Charlemagne'},
        ],
        'selected': [2, 3],
    }
    vpn_api.profile.list.assert_called_once_with()


@pytest.mark.parametrize('route', ('ajout_utilisateurs', 'modif_utilisateurs'))
def test_anciennes_routes_refusent_attribution_vpn(
    rights_application: ModuleType, # pylint: disable=W0621
    route: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None: # pylint: disable=W0621
    """Les anciens formulaires ne doivent pas contourner la synchronisation VPN."""
    with rights_application.peraudiere.test_request_context(
        '/', method='POST', data={'identifiant': 'alice', 'habil7': '7'}
    ):
        with _test_database(monkeypatch, MagicMock()):
            with pytest.raises(BadRequest): # NOSONAR
                getattr(rights_application, route).__wrapped__()


def test_modification_utilisateur_conserve_droit_vpn_sans_autres_droits(
    rights_application: ModuleType, # pylint: disable=W0621
    monkeypatch: pytest.MonkeyPatch, # pylint: disable=W0621
) -> None:
    """Un formulaire sans autre habilitation conserve le droit VPN existant."""
    user = User(id=1, prenom='Alice', nom='Test', identifiant='alice',
                mail='alice@example.org', sha_mdp='secret', habilitation=7)
    database = MagicMock()
    database.execute.return_value.scalars.return_value.first.return_value = user
    monkeypatch.setattr(rights_application, 'revoke_user_sessions', _do_nothing)
    with rights_application.peraudiere.test_request_context(
        '/', method='POST', data={'identifiant': 'alice', 'prenom': 'Alice',
                                  'nom': 'Test', 'mail': 'alice@example.org'}
    ):
        with _test_database(monkeypatch, database):
            response = rights_application.modif_utilisateurs.__wrapped__()
    assert response.status_code == 302
    assert user.habilitation == 7


def test_modification_utilisateur_synchronise_identifiant_vpn(
    rights_application: ModuleType, # pylint: disable=W0621
    vpn_database: Session, # pylint: disable=W0621
    monkeypatch: pytest.MonkeyPatch, # pylint: disable=W0621
) -> None:
    """Une modification de l'identifiant VPN programme sa synchronisation."""
    user = _vpn_user(vpn_database)
    user.vpn_uuid = '12345678-1234-4234-8234-123456789abc'
    user.vpn_sync_state = 'synced'
    vpn_database.commit()
    synced: list[int] = []
    monkeypatch.setattr(rights_application, 'revoke_user_sessions', _do_nothing)

    def record_sync(_database: Session, user_id: int) -> None:
        synced.append(user_id)

    monkeypatch.setattr(rights_application, 'sync_user', record_sync)
    with rights_application.peraudiere.test_request_context(
        '/', method='POST', data={
            'user_id': '1',
            'identifiant': 'alice-nouveau', 'prenom': 'Alice', 'nom': 'Test',
            'mail': 'alice-nouveau@example.org',
        }
    ):
        with _test_database(monkeypatch, vpn_database):
            response = rights_application.modif_utilisateurs.__wrapped__()

    assert response.status_code == 302
    assert user.identifiant == 'alice-nouveau'
    assert user.vpn_sync_state == 'pending'
    assert synced == [1]


def test_activation_depuis_gestion_droits(
    vpn_database: Session, # pylint: disable=W0621
    vpn_api: MagicMock, # pylint: disable=W0621
    rights_application: ModuleType, # pylint: disable=W0621
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """L'activation crée le compte et affecte les profils sélectionnés."""
    import app.ttlama as vpn_service # pylint: disable=C0415

    user = _vpn_user(vpn_database)
    user.habilitation = 1
    user.vpn_sync_state = None
    vpn_database.commit()
    monkeypatch.setattr(rights_application, 'admin_client', vpn_service.admin_client)
    monkeypatch.setattr(rights_application, 'revoke_user_sessions', _do_nothing)
    with rights_application.peraudiere.test_request_context(
        '/', method='POST', data={'identifiant': 'alice', 'habil1': '1', 'habil7': '7',
                                  'vpn_profiles_loaded': '1', 'vpn_profiles': '1'}
    ):
        with _test_database(monkeypatch, vpn_database):
            response = rights_application.gestion_droits_post.__wrapped__()
    assert response.status_code == 302
    assert 'success_message=' in response.location
    assert user.habilitation == 17
    assert user.vpn_sync_state == 'synced'
    vpn_api.user.assign_profile.assert_has_calls([
        call(user.vpn_uuid, 1),
        call(user.vpn_uuid, 2),
    ])


def test_activation_refuse_profil_sdk_indisponible(
    vpn_database: Session, # pylint: disable=W0621
    vpn_api: MagicMock, # pylint: disable=W0621
    rights_application: ModuleType, # pylint: disable=W0621
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un profil requis absent du SDK ne modifie ni les droits ni le compte distant."""
    import app.ttlama as vpn_service # pylint: disable=C0415

    user = _vpn_user(vpn_database)
    user.habilitation = 1
    user.vpn_sync_state = None
    vpn_database.commit()
    vpn_api.profile.list.return_value = [
        {'id': 1, 'name': 'Administrateur', 'revoked_at': None},
    ]
    monkeypatch.setattr(rights_application, 'admin_client', vpn_service.admin_client)
    with rights_application.peraudiere.test_request_context(
        '/',
        method='POST',
        data={
            'identifiant': 'alice',
            'habil1': '1',
            'habil7': '7',
            'vpn_profiles_loaded': '1',
            'vpn_profiles': '99'
        }
    ):
        with _test_database(monkeypatch, vpn_database):
            response = rights_application.gestion_droits_post.__wrapped__()
    assert 'error_message=' in response.location
    assert _vpn_user(vpn_database).habilitation == 1
    vpn_api.user.create.assert_not_called()


def test_gestionnaire_peut_modifier_les_droits(
    app: Flask,
    client: FlaskClient,
    db_session: Session,
    create_multiple_users: list[User],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le rôle gestionnaire conserve l'accès POST historique à la gestion des droits."""
    manager = create_multiple_users[1]
    target = create_multiple_users[0]
    monkeypatch.setitem(app.config, 'WTF_CSRF_ENABLED', False)
    auth_token = create_auth_session(db_session, manager.id)
    db_session.commit()
    with client.session_transaction(base_url='https://localhost') as browser_session:
        browser_session['auth_token'] = auth_token

    response = client.post(
        '/gestion-droits',
        data={'identifiant': target.identifiant, 'habil1': '1'},
        base_url='https://localhost',
    )

    assert response.status_code == 302
    assert 'success_message' in response.headers['Location']


def test_erreur_affectation_reste_en_attente(
    vpn_database: Session, vpn_api: MagicMock, # pylint: disable=W0621
) -> None:
    """Une attribution échouée conserve l'UUID et peut être rejouée."""
    vpn_api.user.assign_profile.side_effect = VPNSyncError('indisponible')
    with pytest.raises(VPNSyncError):
        sync_user(vpn_database, 1)
    user = _vpn_user(vpn_database)
    assert user.vpn_uuid == '12345678-1234-4234-8234-123456789abc'
    assert user.vpn_sync_state == 'pending'
    vpn_api.user.assign_profile.side_effect = None
    sync_user(vpn_database, 1)
    assert user.vpn_sync_state == 'synced'
    vpn_api.user.create.assert_called_once()


def test_mot_de_passe_change_pendant_creation(
    vpn_database: Session, vpn_api: MagicMock, # pylint: disable=W0621
) -> None:
    """Le nouveau hash est synchronisé si la création utilise l'ancien."""
    def create_user(*_args: object, **_kwargs: object) -> dict[str, str]:
        user = _vpn_user(vpn_database)
        user.sha_mdp = 'nouveau-secret'
        vpn_database.commit()
        return {'id': '12345678-1234-4234-8234-123456789abc'}

    vpn_api.user.create.side_effect = create_user
    sync_user(vpn_database, 1)
    user = _vpn_user(vpn_database)
    vpn_api.user.update.assert_called_once_with(
        user.vpn_uuid,
        username='alice',
        email='alice@example.org',
        password='nouveau-secret',
    )
    assert user.vpn_sync_state == 'synced'
    assert not user.vpn_password_dirty
