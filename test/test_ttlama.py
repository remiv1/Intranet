"""Tests locaux du service TTL-LAMa sans accès réseau ni base réelle."""

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from importlib import import_module
from types import ModuleType
from typing import cast
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
from app.ttlama import VPNSyncError, profiles_for_habilitation, sync_user, user_client


def test_client_vpn_utilisateur_verifie_identite(monkeypatch: pytest.MonkeyPatch) -> None:
    """La session ne donne accès qu'au compte distant lié à l'utilisateur."""
    remote = MagicMock()
    remote.me.get.return_value = {'user': {'id': '12345678-1234-4234-8234-123456789abc'}}
    def create_client(*_args: object, **_kwargs: object) -> MagicMock:
        return remote

    monkeypatch.setattr('app.ttlama.TTLLama', create_client)
    monkeypatch.setattr('app.ttlama.ConfigTTLLama.URL', 'https://vpn.example.org')
    user = User(identifiant='alice', sha_mdp='secret-technique', vpn_sync_state='synced',
                vpn_password_dirty=False, vpn_uuid='12345678-1234-4234-8234-123456789abc')
    with user_client(user) as client:
        assert client is remote
    remote.login.assert_called_once_with('alice', 'secret-technique')
    remote.auth.logout.assert_called_once()
    remote.close.assert_called_once()

    remote.me.get.return_value = {'user': {'id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'}}
    mismatched_client = user_client(user)
    with pytest.raises(VPNSyncError, match='incohérente'):
        mismatched_client.__enter__()
    assert remote.close.call_count == 2


@pytest.fixture
def vpn_routes(monkeypatch: pytest.MonkeyPatch) -> tuple[FlaskClient, MagicMock]:
    """Exerce le blueprint sans connexion réseau ni base de données."""
    from app.blueprints.vpn import vpn_bp  # pylint: disable=C0415

    remote = MagicMock()
    remote.me.overview.return_value = {
        'devices': [{'id': 10, 'revoked_at': None}],
        'profiles': [{'id': 2, 'name': 'Fichiers', 'policy': {
            'default_duration': '1h', 'maximum_duration': '2h',
        }}],
        'leases': [{'id': identifier, 'created_at': f'2026-01-{identifier:02}T00:00:00Z',
                    'status': 'expired'} for identifier in range(1, 8)],
    }
    remote.me.devices.list.return_value = [{'id': 10, 'name': 'Portable'}]
    remote.me.leases.create.return_value = {'id': 8, 'status': 'active'}

    @contextmanager
    def fake_user_client(_user: User) -> Generator[MagicMock, None, None]:
        yield remote

    monkeypatch.setattr('app.blueprints.vpn.user_client', fake_user_client)
    application = Flask(__name__)
    application.secret_key = 'test-secret'
    application.register_blueprint(vpn_bp)

    @application.before_request
    def set_user() -> None:
        g.current_user = User(vpn_uuid='12345678-1234-4234-8234-123456789abc')

    client = application.test_client()
    with client.session_transaction() as browser_session:
        browser_session['habilitation'] = '7'
    return client, remote


def test_routes_vpn_baux_validation_et_historique(
    vpn_routes: tuple[FlaskClient, MagicMock],  # pylint: disable=W0621
) -> None:
    """Teste la validation des baux VPN et l'affichage de l'historique."""
    client, remote = vpn_routes
    response = client.get('/vpn/api/state')
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    state = cast(dict[str, object], response.get_json())
    leases = cast(list[dict[str, object]], state['leases'])
    assert [lease['id'] for lease in leases] == [7, 6, 5, 4, 3]

    response = client.post('/vpn/api/leases', json={
        'device_id': 10, 'profile_id': 2, 'duration_minutes': 120,
    })
    assert response.status_code == 201
    remote.me.leases.create.assert_called_once_with(10, 2, duration='120m')
    invalid_payloads: tuple[dict[str, object], ...] = (
        {'device_id': 10, 'profile_id': 2, 'duration_minutes': 121},
        {'device_id': 99, 'profile_id': 2, 'duration_minutes': 60},
        {'device_id': 10, 'profile_id': 99, 'duration_minutes': 60},
        {'device_id': 10, 'profile_id': 2, 'duration_minutes': True},
        {'device_id': 10, 'profile_id': 2, 'duration_minutes': 60, 'private_key': 'secret'},
    )
    for data in invalid_payloads:
        assert client.post('/vpn/api/leases', json=data).status_code == 400
    assert remote.me.leases.create.call_count == 1


def test_routes_vpn_operations_et_incertitude(
    vpn_routes: tuple[FlaskClient, MagicMock],  # pylint: disable=W0621
) -> None:
    """Teste les opérations VPN et la gestion des erreurs."""
    client, remote = vpn_routes
    public_key = 'A' * 43 + '='
    remote.me.devices.create.return_value = {'id': 12, 'public_key': public_key}
    assert client.post('/vpn/api/devices', json={
        'name': 'Portable', 'public_key': public_key,
    }).status_code == 201
    assert client.post('/vpn/api/devices', json={
        'name': 'Portable', 'public_key': public_key, 'private_key': 'secret',
    }).status_code == 400
    assert client.post('/vpn/api/devices/12/delete', json={}).status_code == 200
    remote.me.devices.delete.assert_called_once_with(12)
    remote.me.leases.configuration.return_value = {'configuration_template': 'public'}
    assert client.get('/vpn/api/leases/8/configuration').json == {
        'configuration_template': 'public',
    }
    remote.me.leases.revoke.side_effect = APIError('secret', status_code=503, lease_id=8)
    response = client.post('/vpn/api/leases/8/revoke', json={})
    assert response.status_code == 503
    error_body = cast(dict[str, object], response.get_json())
    assert error_body['lease_id'] == 8
    assert 'secret' not in response.get_data(as_text=True)
    remote.me.leases.revoke.assert_called_once_with(8)


def test_routes_vpn_protegent_csrf_et_habilitation() -> None:
    """Teste la protection CSRF et l'habilitation pour les routes VPN."""
    from flask_wtf import CSRFProtect  # pylint: disable=C0415
    from app.blueprints.vpn import vpn_bp  # pylint: disable=C0415

    application = Flask(__name__)
    application.secret_key = 'test-secret'
    CSRFProtect(application)
    application.register_blueprint(vpn_bp)

    @application.get('/logout')
    def logout() -> str:
        return 'logout'

    client = application.test_client()
    with client.session_transaction() as browser_session:
        browser_session['habilitation'] = '7'
    assert client.post('/vpn/api/leases', json={}).status_code == 400
    with client.session_transaction() as browser_session:
        browser_session['habilitation'] = '1'
    assert client.get('/vpn/api/state').status_code == 302


def test_routes_vpn_session_reelle_et_csrf(
    client: FlaskClient,
    db_session: Session,
    create_admin_user: User,
    authenticated_session_data: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Utilise la session authentifiée réelle et le jeton CSRF de la page."""
    import re  # pylint: disable=C0415

    create_admin_user.habilitation = 17
    create_admin_user.vpn_uuid = '12345678-1234-4234-8234-123456789abc'
    create_admin_user.vpn_sync_state = 'synced'
    create_admin_user.vpn_password_dirty = False
    db_session.commit()
    remote = MagicMock()
    remote.me.devices.create.return_value = {'id': 12}

    @contextmanager
    def fake_user_client(user: User) -> Generator[MagicMock, None, None]:
        assert user.id == create_admin_user.id
        yield remote

    monkeypatch.setattr('app.blueprints.vpn.user_client', fake_user_client)
    with client.session_transaction(base_url='https://localhost') as browser_session:
        browser_session.update(authenticated_session_data)
    page = client.get('/vpn/vpn', base_url='https://localhost')
    assert page.status_code == 200
    token = re.search(r'<meta name="csrf-token" content="([^"]+)">', page.get_data(as_text=True))
    assert token is not None
    body = {'name': 'Portable', 'public_key': 'A' * 43 + '='}
    assert client.post(
        '/vpn/api/devices',
        base_url='https://localhost',
        json=body,
    ).status_code == 400
    response = client.post('/vpn/api/devices', base_url='https://localhost', json=body,
                           headers={'Referer': 'https://localhost/', 'X-CSRFToken': token.group(1)})
    assert response.status_code == 201
    remote.me.devices.create.assert_called_once_with('Portable', body['public_key'])


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
