"""Données et objets persistants pour les tests MariaDB."""

from datetime import date, timedelta
from hashlib import sha256
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.models import Contract, Document, Event, User


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Retourne les données d'un compte de test."""
    return {
        "prenom": "Jean", "nom": "Dupont", "mail": "jean.dupont@test.invalid",
        "identifiant": "jdupont", "sha_mdp": sha256(b"test-password").hexdigest(),
        "habilitation": 1, "debut": date.today(), "fin": None,
        "false_test": 0, "locked": False,
    }


@pytest.fixture
def sample_contract_data() -> dict[str, Any]:
    """Retourne les données d'un contrat valide."""
    return {
        "type_contrat": "Maintenance", "sous_type_contrat": "Informatique",
        "entreprise": "TechCorp", "id_externe_contrat": "TC001",
        "intitule": "Maintenance des serveurs", "date_debut": date.today(),
        "date_fin_preavis": date.today() + timedelta(days=365), "date_fin": None,
    }


@pytest.fixture
def sample_document_data() -> dict[str, Any]:
    """Retourne les données d'un document à rattacher à un contrat."""
    return {
        "type_document": "Contrat", "sous_type_document": "Initial",
        "descriptif": "Contrat initial de maintenance", "str_lien": "contrat_001.pdf",
        "date_document": date.today(), "name": "contrat_001",
    }


@pytest.fixture
def sample_event_data() -> dict[str, Any]:
    """Retourne les données d'un événement à rattacher à un contrat."""
    return {
        "type_evenement": "Renouvellement", "sous_type_evenement": "Automatique",
        "date_evenement": date.today() + timedelta(days=30),
        "descriptif": "Renouvellement automatique du contrat",
    }


@pytest.fixture
def create_test_user(db_session: Session, sample_user_data: dict[str, Any]) -> User:  # pylint: disable=W0621
    """Persiste un utilisateur dans la transaction du test."""
    user = User(**sample_user_data)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def create_admin_user(db_session: Session, sample_user_data: dict[str, Any]) -> User:  # pylint: disable=W0621
    """Persiste un administrateur avec le mot de passe test-password."""
    user = User(**(sample_user_data | {"identifiant": "admin", "prenom": "Admin"}))
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def create_test_contract(db_session: Session, sample_contract_data: dict[str, Any]) -> Contract:  # pylint: disable=W0621
    """Persiste un contrat dans la transaction du test."""
    contract = Contract(**sample_contract_data)
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def create_expiring_contract(db_session: Session, sample_contract_data: dict[str, Any]) -> Contract:  # pylint: disable=W0621
    """Persiste un contrat dont le preavis expire dans trente jours."""
    contract = Contract(**(sample_contract_data | {
        "date_debut": date.today() - timedelta(days=335),
        "date_fin_preavis": date.today() + timedelta(days=30),
    }))
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def create_test_document(
    db_session: Session,
    create_test_contract: Contract,  # pylint: disable=W0621
    sample_document_data: dict[str, Any],  # pylint: disable=W0621
) -> Document:
    """Persiste un document lié au contrat du test."""
    document = Document(**(sample_document_data | {"id_contrat": create_test_contract.id}))
    db_session.add(document)
    db_session.commit()
    return document


@pytest.fixture
def create_test_event(
    db_session: Session,
    create_test_contract: Contract,  # pylint: disable=W0621
    sample_event_data: dict[str, Any],  # pylint: disable=W0621
) -> Event:
    """Persiste un événement lié au contrat du test."""
    event = Event(**(sample_event_data | {"id_contrat": create_test_contract.id}))
    db_session.add(event)
    db_session.commit()
    return event


@pytest.fixture
def create_multiple_users(db_session: Session, sample_user_data: dict[str, Any]) -> list[User]:  # pylint: disable=W0621
    """Persiste quatre utilisateurs avec des habilitations distinctes."""
    users = [
        User(**(sample_user_data | {
            "identifiant": identifier, "prenom": first_name,
            "habilitation": permission, "mail": f"{identifier}@test.invalid",
        }))
        for identifier, first_name, permission in (
            ("jadmin", "Jean", 1), ("mgest", "Marie", 2),
            ("pprof", "Pierre", 4), ("seleve", "Sophie", 5),
        )
    ]
    db_session.add_all(users)
    db_session.commit()
    return users


@pytest.fixture
def create_multiple_contracts(
    db_session: Session,
    sample_contract_data: dict[str, Any],  # pylint: disable=W0621
) -> list[Contract]:
    """Persiste des contrats aux préavis passés, proches et éloignés."""
    contracts = [
        Contract(**(sample_contract_data | {
            "id_externe_contrat": f"TC{index:03}",
            "date_debut": date.today() - timedelta(days=400),
            "date_fin_preavis": date.today() + timedelta(days=days),
        }))
        for index, days in enumerate((65, 120, 200, -30), start=1)
    ]
    db_session.add_all(contracts)
    db_session.commit()
    return contracts


@pytest.fixture
def create_contract_with_documents_and_events(
    db_session: Session,
    create_test_contract: Contract,  # pylint: disable=W0621
    sample_document_data: dict[str, Any],  # pylint: disable=W0621
    sample_event_data: dict[str, Any],  # pylint: disable=W0621
) -> Contract:
    """Persiste deux documents et deux événements liés au même contrat."""
    for index in range(2):
        db_session.add(Document(**(sample_document_data | {
            "id_contrat": create_test_contract.id, "name": f"contrat_{index:03}",
            "str_lien": f"contrat_{index:03}.pdf",
        })))
        db_session.add(Event(**(sample_event_data | {
            "id_contrat": create_test_contract.id, "descriptif": f"Evenement {index}",
        })))
    db_session.commit()
    return create_test_contract


@pytest.fixture
def authenticated_session_data(
    db_session: Session,
    create_admin_user: User,    # pylint: disable=W0621
) -> dict[str, Any]:
    """Retourne les données de session du compte réel de test."""
    from app.repositories.auth_session import create_auth_session   # pylint: disable=C0415

    token = create_auth_session(db_session, create_admin_user.id)
    db_session.commit()
    return {
        "auth_token": token,
        "id": create_admin_user.id, "identifiant": create_admin_user.identifiant,
        "prenom": create_admin_user.prenom, "nom": create_admin_user.nom,
        "mail": create_admin_user.mail, "habilitation": str(create_admin_user.habilitation),
    }
