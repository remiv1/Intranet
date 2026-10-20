"""Configuration des tests executés sur la MariaDB temporaire du Compose de test."""

import os
from collections.abc import Iterator
from importlib import import_module
from pathlib import Path
from typing import Any, NoReturn

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import Engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from alembic.config import Config as AlembicConfig
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory

if (
    os.environ.get("INTRANET_TESTING") != "1"
    or os.environ.get("PYTHON_DOTENV_DISABLED") != "1"
    or os.environ.get("DB_HOST") != "db-test"
    or os.environ.get("DB_NAME") != "intranet_test"
    or os.environ.get("DB_USER") != "intranet_test"
):
    raise pytest.UsageError(
        "Executer les tests dans Docker avec docker-compose.test.yaml. "
        "La base de développement ou de production ne doit jamais être utilisée."
    )

from app.config.config import ConfigApp, ConfigDB   # pylint: disable=C0413
from app.config.database import engine  # pylint: disable=C0413
from app.models._common import Base  # pylint: disable=C0413

if (
    ConfigDB.DB_URL.host != "db-test"
    or ConfigDB.DB_URL.database != "intranet_test"
    or ConfigDB.DB_URL.username != "intranet_test"
):
    raise pytest.UsageError("La configuration chargee ne cible pas la base de test isolee.")

pytest_plugins = ("test.fixtures",)


@pytest.fixture(scope="session")
def database_engine() -> Iterator[Engine]:
    """Initialise le schema uniquement dans la base temporaire autorisee.

    Yields:
        Engine: Moteur SQLAlchemy connecte a MariaDB de test.
    """
    with engine.connect() as connection:
        if connection.scalar(text("SELECT DATABASE()")) != "intranet_test":
            raise pytest.UsageError("Le serveur ne cible pas la base de test attendue.")
    with engine.begin() as connection:
        Base.metadata.create_all(connection, tables=[
            table for table in Base.metadata.sorted_tables if table.name != '98_sessions'
        ])
        assert not inspect(connection).has_table('98_sessions')
        revision = ScriptDirectory.from_config(
            AlembicConfig('alembic.ini')
        ).get_revision('d4f3a20e9b71')
        assert revision is not None
        with Operations.context(MigrationContext.configure(connection)):
            revision.module.upgrade()
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(database_engine: Engine) -> Iterator[Session]:   # pylint: disable=W0621
    """Isole les ecritures du test, meme apres un commit applicatif.

    Args:
        database_engine: Moteur de la base de test.

    Yields:
        Session: Vraie session utilisant des points de sauvegarde MariaDB.
    """
    with database_engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as database_session:
                yield database_session
        finally:
            transaction.rollback()


@pytest.fixture
def app(db_session: Session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Flask:   # pylint: disable=W0621
    """Charge la vraie application avec des sessions rattachees au test.

    Args:
        db_session: Session de la transaction isolee.
        monkeypatch: Restauration des configurations apres le test.
        tmp_path: Repertoire temporaire propre au test.

    Returns:
        Flask: Application configuree sans modifier la configuration de production.
    """
    application = import_module("app.application")
    session_factory = sessionmaker(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    monkeypatch.setattr(application, "SESSION", session_factory)
    monkeypatch.setitem(application.peraudiere.config, "TESTING", True)
    monkeypatch.setitem(application.peraudiere.config, "SECRET_KEY", "test-only-session-secret")
    for setting, directory in (("UPLOAD_FOLDER", "documents"), ("PRINT_PATH", "print")):
        folder = tmp_path / directory
        folder.mkdir()
        monkeypatch.setattr(ConfigApp, setting, str(folder))
        monkeypatch.setitem(application.peraudiere.config, setting, str(folder))
    return application.peraudiere


@pytest.fixture
def client(app: Flask) -> FlaskClient:   # pylint: disable=W0621
    """Cree un client pour les veritables routes Flask.

    Args:
        app: Application configuree pour le test.

    Returns:
        FlaskClient: Client sans serveur HTTP externe.
    """
    return app.test_client()


@pytest.fixture(autouse=True)
def block_external_services(monkeypatch: pytest.MonkeyPatch) -> None:
    """Interdit les effets externes sans remplacer la base de donnees.

    Args:
        monkeypatch: Restauration automatique des fonctions bloquees.
    """
    def forbidden(*args: Any, **kwargs: Any) -> NoReturn:
        raise AssertionError("Email, SSH ou impression reels interdits pendant les tests.")

    monkeypatch.setattr("smtplib.SMTP", forbidden)
    monkeypatch.setattr("smtplib.SMTP_SSL", forbidden)
    monkeypatch.setattr("paramiko.SSHClient", forbidden)
    monkeypatch.setattr("app.impression.print_file", forbidden)
