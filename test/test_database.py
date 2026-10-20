"""Verifications des sessions SQLAlchemy et des contraintes MariaDB reelles."""

from typing import Any

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Contract, Document, User


class TestDatabaseSession:
    """Verifications du stockage, des filtres et des transactions."""

    def test_real_mariadb_session(self, db_session: Session) -> None:
        """Verifie le serveur reel et la base de test ciblee."""
        assert isinstance(db_session, Session)
        assert "MariaDB" in db_session.scalar(text("SELECT VERSION()"))
        assert db_session.scalar(text("SELECT DATABASE()")) == "intranet_test"

    def test_commit_and_reload(self, db_session: Session, create_test_user: User) -> None:
        """Verifie la relecture depuis MariaDB apres un commit."""
        identifier = create_test_user.id
        db_session.expunge_all()

        stored_user = db_session.get(User, identifier)

        assert stored_user is not None
        assert stored_user is not create_test_user
        assert stored_user.identifiant == "jdupont"

    def test_query_filters(self, db_session: Session, create_multiple_users: list[User]) -> None:
        """Verifie qu'un filtre SQL exclut les autres utilisateurs."""
        users = db_session.scalars(select(User).where(User.identifiant == "mgest")).all()

        assert users == [create_multiple_users[1]]

    def test_rollback(self, db_session: Session, sample_user_data: dict[str, Any]) -> None:
        """Verifie qu'un rollback retire les ecritures non validees."""
        db_session.add(User(**sample_user_data))
        db_session.flush()
        assert len(db_session.scalars(select(User)).all()) == 1

        db_session.rollback()

        assert db_session.scalars(select(User)).all() == []

    def test_generated_ids(self, db_session: Session, create_multiple_users: list[User]) -> None:
        """Verifie l'unicite des identifiants sans supposer leur remise a zero."""
        identifiers = [user.id for user in create_multiple_users]

        assert all(identifier > 0 for identifier in identifiers)
        assert len(set(identifiers)) == 4
        assert len(db_session.scalars(select(User)).all()) == 4

    def test_multiple_models(
        self, db_session: Session, create_test_user: User, create_test_contract: Contract
    ) -> None:
        """Verifie la sauvegarde des modeles dans leurs tables respectives."""
        assert db_session.scalars(select(User)).all() == [create_test_user]
        assert db_session.scalars(select(Contract)).all() == [create_test_contract]

    def test_document_requires_existing_contract(
        self, db_session: Session, sample_document_data: dict[str, Any]
    ) -> None:
        """Verifie qu'une vraie cle etrangere refuse un contrat inexistant."""
        db_session.add(Document(**(sample_document_data | {"id_contrat": -1})))

        with pytest.raises(IntegrityError):
            db_session.flush()

        db_session.rollback()