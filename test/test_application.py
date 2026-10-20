"""Tests des modèles et des routes existantes sur MariaDB."""

from datetime import date, timedelta
from typing import Any
from urllib.parse import urlsplit

import pytest
from flask.testing import FlaskClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contract, Document, Event, User


class TestUserOperations:
    """Tests pour les opérations sur les utilisateurs."""

    def test_create_user(self, db_session: Session, sample_user_data: dict[str, Any]) -> None:
        """Vérifie la sauvegarde puis la relecture d'un utilisateur."""
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        db_session.expire_all()

        stored_user = db_session.get(User, user.id)
        assert stored_user is not None
        assert stored_user.prenom == "Jean"
        assert stored_user.nom == "Dupont"
        assert stored_user.mail == "jean.dupont@test.invalid"

    def test_query_users(self, db_session: Session, create_multiple_users: list[User]) -> None:
        """Vérifie la liste et les identifiants générés par MariaDB."""
        users = db_session.scalars(select(User).order_by(User.id)).all()

        assert len(users) == 4
        assert [user.id for user in users] == [user.id for user in create_multiple_users]
        assert db_session.get(User, create_multiple_users[0].id) == create_multiple_users[0]

    def test_admin_lookup(self, db_session: Session, create_admin_user: User) -> None:
        """Vérifie la recherche du compte, sans simuler une authentification."""
        user = db_session.scalar(select(User).where(User.identifiant == "admin"))
        assert user is not None

        assert user is create_admin_user
        assert user.habilitation == 1


class TestContractOperations:
    """Tests pour les opérations sur les contrats."""

    def test_create_contract(
            self, db_session: Session,
            sample_contract_data: dict[str, Any],
        ) -> None:
        """Vérifie la persistance des informations d'un contrat."""
        contract = Contract(**sample_contract_data)
        db_session.add(contract)
        db_session.commit()
        db_session.expire_all()

        stored_contract = db_session.get(Contract, contract.id)
        assert stored_contract is not None
        assert stored_contract.entreprise == "TechCorp"
        assert stored_contract.type_contrat == "Maintenance"

    def test_expiring_contracts(
        self, db_session: Session, create_multiple_contracts: list[Contract]
    ) -> None:
        """Vérifie un filtre SQL entre aujourd'hui et quatre-vingt-dix jours."""
        contracts = db_session.scalars(select(Contract).where(
            Contract.date_fin_preavis.between(date.today(), date.today() + timedelta(days=90))
        )).all()

        assert contracts == [create_multiple_contracts[0]]

    def test_contract_with_relations(
        self, db_session: Session, create_contract_with_documents_and_events: Contract
    ) -> None:
        """Vérifie les clés étrangères et le chargement des relations."""
        contract = create_contract_with_documents_and_events
        db_session.expire_all()
        stmt_doc = select(Document).where(Document.id_contrat == contract.id)
        documents = db_session.scalars(stmt_doc).all()
        stmt_event = select(Event).where(Event.id_contrat == contract.id)
        events = db_session.scalars(stmt_event).all()

        assert len(documents) == 2
        assert len(events) == 2
        assert {
            document.id for document in contract.documents
        } == {
            document.id for document in documents
        }
        assert {event.id for event in contract.evenements} == {event.id for event in events}


class TestFlaskRoutes:
    """Tests pour les routes Flask."""

    def test_login_page(self, client: FlaskClient) -> None:
        """Test de la page de connexion."""
        response = client.get('/login', base_url="https://localhost")
        assert response.status_code == 200
        assert 'name="csrf_token"' in response.get_data(as_text=True)

    def test_index_redirect_when_not_authenticated(self, client: FlaskClient) -> None:
        """Verifie la redirection effective d'un client sans session."""
        response = client.get('/', base_url="https://localhost")

        assert response.status_code == 302
        assert urlsplit(response.headers["Location"]).path == "/login"

    def test_authenticated_access(
        self, client: FlaskClient, authenticated_session_data: dict[str, Any]
    ) -> None:
        """Verifie l'accueil avec une session rattachee au compte de test."""
        with client.session_transaction(base_url="https://localhost") as user_session:
            user_session.update(authenticated_session_data)

        response = client.get('/', base_url="https://localhost")

        assert response.status_code == 200


class TestDataIntegrity:
    """Tests pour l'intégrité des données."""

    @pytest.mark.parametrize("execution", (1, 2))
    def test_database_isolation(
        self, db_session: Session, sample_user_data: dict[str, Any], execution: int
    ) -> None:
        """Verifie qu'un commit du cas precedent ne laisse aucune ligne."""
        assert db_session.scalars(select(User)).all() == []

        user = User(**(sample_user_data | {"identifiant": f"isolated-{execution}"}))
        db_session.add(user)
        db_session.commit()

        assert db_session.scalars(select(User)).all() == [user]
