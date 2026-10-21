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


@pytest.fixture
def manager_client(
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

    created = db_session.scalar(select(model).where(model.id_contrat == create_test_contract.id))
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
