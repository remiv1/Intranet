"""Verifications des sessions SQLAlchemy et des contraintes MariaDB reelles."""

from collections.abc import Iterator
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.engine import Connection

from app.models import Contract, Document, User


@pytest.fixture(name='contact_migration')
def contact_migration_fixture() -> Iterator[tuple[Connection, ModuleType]]:
    """Ancien schéma isolé pour exercer la migration sans altérer MariaDB des fixtures."""
    import sqlalchemy as sa # pylint: disable=C0415
    from alembic.config import Config # pylint: disable=C0415
    from alembic.migration import MigrationContext # pylint: disable=C0415
    from alembic.operations import Operations # pylint: disable=C0415
    from alembic.script import ScriptDirectory # pylint: disable=C0415

    engine = sa.create_engine('sqlite://')
    metadata = sa.MetaData()
    contracts = sa.Table('01_contrats', metadata, sa.Column('id', sa.Integer, primary_key=True))
    contacts = sa.Table('02_contacts', metadata, sa.Column('id', sa.Integer, primary_key=True),
                        sa.Column('nom', sa.String(255)),
                        sa.Column('id_contrat', sa.Integer, sa.ForeignKey('01_contrats.id'),
                                  nullable=False))
    revision = ScriptDirectory.from_config(Config('alembic.ini')).get_revision('a7c9d2e4f601')
    assert revision is not None
    with engine.begin() as connection:
        metadata.create_all(connection)
        connection.execute(contracts.insert(), [{'id': 1}, {'id': 2}])
        connection.execute(contacts.insert(), [{'id': 1, 'nom': 'Premier', 'id_contrat': 1},
                                               {'id': 2, 'nom': 'Second', 'id_contrat': 2}])
        with Operations.context(MigrationContext.configure(connection)):
            yield connection, revision.module
    engine.dispose()


def test_contact_migration_preserves_existing_links(
    contact_migration: tuple[Connection, ModuleType],
) -> None:
    """L'upgrade et le downgrade 1:1 ne perdent ni fiches ni associations."""
    from sqlalchemy import inspect # pylint: disable=C0415

    connection, migration = contact_migration
    migration.upgrade()
    assert connection.execute(
        text(
            'SELECT * FROM "02_contacts_contrats" ORDER BY id_contact'
        )
    ).all() == [(1, 1), (2, 2)]
    assert 'id_contrat' not in {
        column['name'] for column in inspect(connection).get_columns('02_contacts')
    }
    migration.downgrade()
    assert connection.execute(
        text('SELECT id, id_contrat FROM "02_contacts" ORDER BY id')
    ).all() == [(1, 1), (2, 2)]


@pytest.mark.parametrize('multiple', [False, True])
def test_contact_migration_refuses_lossy_downgrade(
    contact_migration: tuple[Connection, ModuleType], multiple: bool,
) -> None:
    """Un contact indépendant ou partagé bloque un downgrade avant toute modification."""
    from sqlalchemy import inspect # pylint: disable=C0415

    connection, migration = contact_migration
    migration.upgrade()
    if multiple:
        connection.execute(text('INSERT INTO "02_contacts_contrats" VALUES (1, 2)'))
    else:
        connection.execute(text('DELETE FROM "02_contacts_contrats" WHERE id_contact = 1'))
    with pytest.raises(RuntimeError, match='exactement un contrat'):
        migration.downgrade()
    assert 'id_contrat' not in {
        column['name'] for column in inspect(connection).get_columns('02_contacts')
    }
    assert connection.execute(text('SELECT COUNT(*) FROM "02_contacts"')).scalar() == 2


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