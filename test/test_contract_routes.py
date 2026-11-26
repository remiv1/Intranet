"""Tests des routes de gestion des contrats."""

from io import BytesIO
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from app.models import Bill, Contacts, Contract, Document, Event, User
from app.repositories.auth_session import create_auth_session


def test_contact_book_creates_independent_contact(
    manager_client: FlaskClient, # pylint: disable=W0621
    db_session: Session,
) -> None:
    """Une fiche peut exister sans contrat et reste accessible dans le carnet."""
    response = manager_client.post('/ea/contacts/nouveau', base_url='https://localhost',
                                   data={'nomC': 'Contact autonome', 'mailC': 'alone@test.invalid'})
    assert response.status_code == 302
    contact = db_session.scalar(select(Contacts).where(Contacts.nom == 'Contact autonome'))
    assert contact is not None
    assert contact.contrats == []
    page = manager_client.get('/ea/contacts', base_url='https://localhost')
    assert page.status_code == 200
    assert 'Sans contrat' in page.get_data(as_text=True)
    assert 'Supprimer définitivement cette fiche' in page.get_data(as_text=True)


def test_contact_book_multiple_contracts_and_detachment(
    manager_client: FlaskClient, # pylint: disable=W0621
    db_session: Session,
    create_multiple_contracts: list[Contract],
) -> None:
    """Détacher un contact laisse sa fiche et son autre association intactes."""
    first, second = create_multiple_contracts[:2]
    response = manager_client.post('/ea/contacts/nouveau', base_url='https://localhost', data={
        'nomC': 'Contact partagé', 'mailC': 'shared@test.invalid',
        'contrats': [str(first.id), str(second.id), str(first.id)],
    })
    assert response.status_code == 302
    contact = db_session.scalar(select(Contacts).where(Contacts.nom == 'Contact partagé'))
    assert contact is not None
    assert {contract.id for contract in contact.contrats} == {first.id, second.id}
    detail = manager_client.get(f'/contrats/contrat-{first.id}', base_url='https://localhost')
    assert detail.status_code == 200
    assert 'Contact partagé' in detail.get_data(as_text=True)
    assert 'Retirer Contact partagé du contrat' in detail.get_data(as_text=True)
    response = manager_client.post(
        f'/contrats/contrat-{first.id}/contact-{contact.id}/supprimer',
        base_url='https://localhost', data={'contact_id': str(contact.id)},
    )
    assert response.status_code == 302
    db_session.expire_all()
    assert db_session.get(Contacts, contact.id) is not None
    assert [contract.id for contract in contact.contrats] == [second.id]
    assert manager_client.post(
        f'/contrats/contrat-{first.id}/contact-{contact.id}/supprimer',
        base_url='https://localhost', data={'contact_id': str(contact.id)},
    ).status_code == 404


def test_contact_book_delete_preserves_contracts(
    manager_client: FlaskClient, # pylint: disable=W0621
    db_session: Session,
    create_multiple_contracts: list[Contract],
) -> None:
    """La suppression du carnet retire fiche et liens, jamais les contrats."""
    from app.models.contacts import contacts_contrats # pylint: disable=C0415

    contact = Contacts(nom='Supprimable', mail='delete@test.invalid',
                       contrats=create_multiple_contracts[:2])
    db_session.add(contact)
    db_session.commit()
    identifier = contact.id
    response = manager_client.post(
        f'/ea/contacts/{identifier}/supprimer',
        base_url='https://localhost',
        data={'contact_id': str(identifier)},
    )
    assert response.status_code == 302
    db_session.expire_all()
    assert db_session.get(Contacts, identifier) is None
    assert db_session.execute(select(contacts_contrats).where(
        contacts_contrats.c.id_contact == identifier
    )).all() == []
    assert len(db_session.scalars(select(Contract)).all()) == len(create_multiple_contracts)


def test_contact_association_is_idempotent_and_modification_is_shared(
    manager_client: FlaskClient, # pylint: disable=W0621
    db_session: Session,
    create_multiple_contracts: list[Contract],
) -> None:
    """Rattacher deux fois ne duplique pas ; éditer ne réaffecte pas le contact."""
    first, second, other = create_multiple_contracts[:3]
    contact = Contacts(nom='Avant', mail='before@test.invalid', contrats=[first])
    db_session.add(contact)
    db_session.commit()
    for _attempt in range(2):
        assert manager_client.post(
            f'/contrats/contrat-{second.id}/contact/rattacher',
            base_url='https://localhost',
            data={'contact_id': str(contact.id)},
        ).status_code == 302
    response = manager_client.post(
        f'/contrats/contrat-{first.id}/contact-{contact.id}', base_url='https://localhost',
        data={'nomC': 'Après', 'mailC': 'after@test.invalid'},
    )
    assert response.status_code == 302
    db_session.expire_all()
    assert contact.nom == 'Après'
    assert {contract.id for contract in contact.contrats} == {first.id, second.id}
    assert manager_client.post(
        f'/contrats/contrat-{other.id}/contact-{contact.id}',
        base_url='https://localhost',
        data={'nomC': 'Interdit', 'mailC': 'invalid@test.invalid'},
    ).status_code == 404
    assert manager_client.post(
        f'/contrats/contrat-{other.id}/contact-{contact.id}/supprimer',
        base_url='https://localhost',
        data={'contact_id': str(contact.id)},
    ).status_code == 404


def test_contact_book_updates_associations_and_rejects_invalid_selection(
    manager_client: FlaskClient, # pylint: disable=W0621
    db_session: Session,
    create_multiple_contracts: list[Contract],
) -> None:
    """Modifier une fiche remplace la sélection, sans accepter de contrat inexistant."""
    contact = Contacts(
        nom='Fiche',
        mail='contact@test.invalid',
        contrats=create_multiple_contracts[:2],
    )
    db_session.add(contact)
    db_session.commit()
    page = manager_client.get(f'/ea/contacts/{contact.id}', base_url='https://localhost')
    assert page.status_code == 200
    for invalid in ('-1', 'invalide'):
        response = manager_client.post(f'/ea/contacts/{contact.id}', base_url='https://localhost',
                                       data={'nomC': 'Autre', 'mailC': 'new@test.invalid',
                                             'contrats': [invalid]})
        assert response.status_code == 400
    db_session.refresh(contact)
    assert contact.nom == 'Fiche'
    assert len(contact.contrats) == 2
    response = manager_client.post(f'/ea/contacts/{contact.id}', base_url='https://localhost',
                                   data={'nomC': 'Fiche libre', 'mailC': 'contact@test.invalid'})
    assert response.status_code == 302
    db_session.expire_all()
    assert contact.contrats == []
    assert contact.nom == 'Fiche libre'
    assert manager_client.post(
        '/ea/contacts/nouveau',
        base_url='https://localhost',
        data={'nomC': '', 'mailC': 'contact@test.invalid'}
    ).status_code == 400


def test_contact_book_search_and_administrative_navigation(
    manager_client: FlaskClient,
    db_session: Session,
) -> None:
    """Les modules sont regroupés dans /ea et la recherche ne traite pas % comme un joker."""
    db_session.add_all([Contacts(nom='Visible', mail='visible@test.invalid'),
                        Contacts(nom='Autre', mail='other@test.invalid')])
    db_session.commit()
    page = manager_client.get('/ea/contacts?q=Visible', base_url='https://localhost')
    assert page.status_code == 200
    assert 'mailto:visible@test.invalid' in page.get_data(as_text=True)
    assert 'mailto:other@test.invalid' not in page.get_data(as_text=True)
    page = manager_client.get('/ea/contacts?q=%25', base_url='https://localhost')
    assert 'mailto:' not in page.get_data(as_text=True)
    home = manager_client.get('/', base_url='https://localhost').get_data(as_text=True)
    administrative = manager_client.get('/ea', base_url='https://localhost').get_data(as_text=True)
    assert 'href="/contrats/"' not in home
    assert 'href="/contrats/"' in administrative
    assert 'href="/ea/contacts"' in administrative


@pytest.mark.parametrize('path', ['/ea/contacts', '/ea/contacts/nouveau', '/ea/contacts/1'])
def test_contact_book_requires_manager(
    client: FlaskClient,
    db_session: Session,
    create_multiple_users: list[User],
    path: str,
) -> None:
    """Le carnet est inaccessible aux utilisateurs sans habilitation gestionnaire."""
    token = create_auth_session(db_session, create_multiple_users[3].id)
    db_session.commit()
    with client.session_transaction(base_url='https://localhost') as browser_session:
        browser_session['auth_token'] = token
    assert client.get(path, base_url='https://localhost').status_code == 302


def test_contact_mutations_require_csrf(
    app: Flask,
    manager_client: FlaskClient,
    db_session: Session,
    create_test_contract: Contract,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Les mutations du carnet et des associations conservent la protection CSRF."""
    import re # pylint: disable=C0415

    contact = Contacts(nom='Protégé', mail='csrf@test.invalid', contrats=[create_test_contract])
    db_session.add(contact)
    db_session.commit()
    monkeypatch.setitem(app.config, 'WTF_CSRF_ENABLED', True)
    for path in ('/ea/contacts/nouveau', f'/ea/contacts/{contact.id}',
                 f'/ea/contacts/{contact.id}/supprimer',
                 f'/contrats/contrat-{create_test_contract.id}/contact/rattacher',
                 f'/contrats/contrat-{create_test_contract.id}/contact-{contact.id}/supprimer'):
        assert manager_client.post(path, base_url='https://localhost', json={}).status_code == 400
    page = manager_client.get(f'/ea/contacts/{contact.id}', base_url='https://localhost')
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.get_data(as_text=True))
    assert token is not None
    response = manager_client.post(f'/ea/contacts/{contact.id}', base_url='https://localhost',
                                   headers={'Referer': 'https://localhost/'},
                                   data={'nomC': 'Validé', 'mailC': 'csrf@test.invalid',
                                         'csrf_token': token.group(1),
                                         'contrats': [str(create_test_contract.id)]})
    assert response.status_code == 302


@pytest.fixture(name='manager_client')
def manager_client_fixture(
    app: Flask,
    client: FlaskClient,
    db_session: Session,
    create_multiple_users: list[User],
    monkeypatch: pytest.MonkeyPatch,
) -> FlaskClient:
    """Authentifie le gestionnaire et désactive CSRF pour les appels de route ciblés."""
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    auth_token = create_auth_session(db_session, create_multiple_users[1].id)
    db_session.commit()
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["auth_token"] = auth_token
    return client


def test_contract_routes_require_manager_habilitation(
    client: FlaskClient,
    db_session: Session,
    create_multiple_users: list[User],
) -> None:
    """Un élève ne peut pas consulter le module de gestion des contrats."""
    auth_token = create_auth_session(db_session, create_multiple_users[3].id)
    db_session.commit()
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["auth_token"] = auth_token

    response = client.get("/contrats/", base_url="https://localhost")

    assert response.status_code == 302
    assert urlsplit(response.headers["Location"]).path == "/logout"


def test_manager_can_create_and_update_contract(
    manager_client: FlaskClient,    # pylint: disable=W0621
    db_session: Session,
) -> None:
    """Les routes gestionnaire enregistrent une création puis une modification."""
    response = manager_client.post(
        "/contrats/",
        data={
            "Type0": "Maintenance",
            "SType0": "Informatique",
            "Entreprise": "TechCorp",
            "numContratExterne": "TC-ROUTE-1",
            "Intitule": "Contrat initial",
            "dateDebut": date.today().isoformat(),
            "dateFinPreavis": date.today().isoformat(),
            "dateFin": "",
        },
        base_url="https://localhost",
    )
    contract = db_session.scalar(
        select(Contract).where(Contract.id_externe_contrat == "TC-ROUTE-1")
    )
    assert response.status_code == 302
    assert contract is not None
    assert "success_message" in urlsplit(response.headers["Location"]).query

    response = manager_client.post(
        f"/contrats/contrat-{contract.id}",
        data={
            "Type0": "Maintenance",
            "SType0": "Informatique",
            "Entreprise": "TechCorp",
            "numContratExterne": "TC-ROUTE-1",
            "Intitule": "Contrat modifié",
            "dateDebut": date.today().isoformat(),
            "dateFinPreavis": date.today().isoformat(),
            "dateFin": "",
        },
        base_url="https://localhost",
    )

    db_session.refresh(contract)
    assert response.status_code == 302
    assert contract.intitule == "Contrat modifié"


@pytest.mark.parametrize(
    ("endpoint", "data", "model", "expected_value"),
    (
        (
            "contact",
            {"nomC": "Contact route", "mailC": "contact@test.invalid"},
            Contacts,
            "Contact route",
        ),
        (
            "evenement",
            {
                "dateEvenementE": date.today().isoformat(),
                "TypeE0": "Suivi",
                "STypeE0": "Rendez-vous",
                "descriptifE": "Événement de test",
            },
            Event,
            "Événement de test",
        ),
    ),
)
def test_manager_can_add_contract_contacts_and_events(
    manager_client: FlaskClient,    # pylint: disable=W0621
    db_session: Session,
    create_test_contract: Contract,
    endpoint: str,
    data: dict[str, Any],
    model: type[Contacts] | type[Event],
    expected_value: str,
) -> None:
    """Les routes d’ajout persistents les contacts et événements associés."""
    response = manager_client.post(
        f"/contrats/contrat-{create_test_contract.id}/{endpoint}",
        data=data,
        base_url="https://localhost",
    )

    if model is Contacts:
        created = db_session.scalar(select(Contacts).where(
            Contacts.contrats.any(Contract.id == create_test_contract.id)
        ))
    else:
        created = db_session.scalar(
            select(Event).where(Event.id_contrat == create_test_contract.id)
        )
    assert response.status_code == 302
    assert created is not None
    assert (created.nom if isinstance(created, Contacts) else created.descriptif) == expected_value


@pytest.mark.parametrize(
    ("endpoint", "model", "form_data"),
    (
        (
            "document",
            Document,
            {
                "dateDocumentD": date.today().isoformat(),
                "TypeD0": "Contrat",
                "STypeD0": "Initial",
                "descriptifD": "Document upload test",
                "documentD": (BytesIO(b"document"), "source.pdf"),
            },
        ),
        (
            "facture",
            Bill,
            {
                "dateFactureF0": date.today().isoformat(),
                "titreFactureF0": "Facture test",
                "montantFactureF0": "12.50",
                "documentF0": (BytesIO(b"facture"), "source.pdf"),
            },
        ),
    ),
)
def test_upload_failure_rolls_back_attachment_and_file(
    app: Flask,
    manager_client: FlaskClient,    # pylint: disable=W0621
    db_session: Session,
    create_test_contract: Contract,
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str,
    model: type[Document] | type[Bill],
    form_data: dict[str, Any],
) -> None:
    """Un échec d’upload remonte et ne conserve ni ligne ni fichier partiel."""
    monkeypatch.setattr(
        "app.docs.upload_file",
        lambda *_args,  # type: ignore
        **_kwargs: (_ for _ in ()).throw(OSError("disk full"))  # type: ignore
    )

    with pytest.raises(OSError, match="disk full"):
        manager_client.post(
            f"/contrats/contrat-{create_test_contract.id}/{endpoint}",
            data=form_data,
            content_type="multipart/form-data",
            base_url="https://localhost",
        )

    db_session.expire_all()
    assert db_session.scalars(
        select(model).where(model.id_contrat == create_test_contract.id)
    ).all() == []
    assert list((app.root_path and __import__("pathlib").Path(  # type: ignore # pylint: disable=C1803
        app.config["UPLOAD_FOLDER"]
    )).iterdir()) == [] # type: ignore


@pytest.mark.parametrize(
    ("endpoint", "model", "form_data"),
    (
        (
            "document",
            Document,
            {
                "dateDocumentD": date.today().isoformat(),
                "TypeD0": "Contrat",
                "STypeD0": "Initial",
                "descriptifD": "Commit test",
                "documentD": (BytesIO(b"document"), "source.pdf"),
            },
        ),
        (
            "facture",
            Bill,
            {
                "dateFactureF0": date.today().isoformat(),
                "titreFactureF0": "Commit test",
                "montantFactureF0": "12.50",
                "documentF0": (BytesIO(b"facture"), "source.pdf"),
            },
        ),
    ),
)
def test_commit_failure_restores_attachment_file_state(
    app: Flask,
    manager_client: FlaskClient,    # pylint: disable=W0621
    db_session: Session,
    create_test_contract: Contract,
    endpoint: str,
    model: type[Document] | type[Bill],
    form_data: dict[str, Any],
) -> None:
    """Un échec SQL après l’écriture disque restaure le système de fichiers."""

    def fail_attachment_commit(database_session: Session) -> None:
        if any(isinstance(item, model) for item in database_session.identity_map.values()):
            raise SQLAlchemyError("attachment commit failed")

    event.listen(Session, "before_commit", fail_attachment_commit)
    try:
        with pytest.raises(SQLAlchemyError, match="attachment commit failed"):
            manager_client.post(
                f"/contrats/contrat-{create_test_contract.id}/{endpoint}",
                data=form_data,
                content_type="multipart/form-data",
                base_url="https://localhost",
            )
    finally:
        event.remove(Session, "before_commit", fail_attachment_commit)

    db_session.expire_all()
    assert db_session.scalars(
        select(model).where(model.id_contrat == create_test_contract.id)
    ).all() == []
    assert list(__import__("pathlib").Path(app.config["UPLOAD_FOLDER"]).iterdir()) == []    # pylint: disable=C1803


def test_bill_modification_commit_failure_restores_old_values_and_file(
    app: Flask,
    manager_client: FlaskClient,    # pylint: disable=W0621
    db_session: Session,
    create_test_contract: Contract,
) -> None:
    """Un commit facture en échec restaure les métadonnées et le fichier d’origine."""
    old_path = Path(app.config["UPLOAD_FOLDER"]) / "facture-originale.pdf"  # type: ignore
    old_path.write_bytes(b"contenu original")
    bill = Bill(
        id_contrat=create_test_contract.id,
        date_facture=datetime(2024, 1, 2),
        titre_facture="Facture initiale",
        montant=10,
        str_lien=old_path.name,
        name="facture-originale",
    )
    db_session.add(bill)
    db_session.commit()

    def fail_bill_commit(database_session: Session) -> None:
        if any(isinstance(item, Bill) for item in database_session.identity_map.values()):
            raise SQLAlchemyError("bill commit failed")

    event.listen(Session, "before_commit", fail_bill_commit)
    try:
        def update_bill() -> None:
            manager_client.post(
                f"/contrats/contrat-{create_test_contract.id}/facture-{bill.id}",
                data={
                    "dateFactureF0": date.today().isoformat(),
                    "titreFactureF0": "Facture modifiée",
                    "montantFactureF0": "20",
                    "documentF0": (BytesIO(b"nouveau contenu"), "nouveau.pdf"),
                },
                content_type="multipart/form-data",
                base_url="https://localhost",
            )

        with pytest.raises(SQLAlchemyError, match="bill commit failed"):
            update_bill()
    finally:
        event.remove(Session, "before_commit", fail_bill_commit)

    db_session.expire_all()
    db_session.refresh(bill)
    assert bill.titre_facture == "Facture initiale"
    assert bill.str_lien == old_path.name
    assert old_path.read_bytes() == b"contenu original"
    assert list(Path(app.config["UPLOAD_FOLDER"]).iterdir()) == [old_path]  # type: ignore
