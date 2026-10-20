"""Migration des mots de passe SHA-256 vers Argon2id sur MariaDB reelle."""

import logging
from datetime import date, timedelta
from typing import Any
from test.test_login_redirects import _submit_login # type: ignore

import pytest
from argon2 import PasswordHasher
from flask import Flask, g, session
from flask.testing import FlaskClient
from flask_wtf.csrf import generate_csrf    # type: ignore
from sqlalchemy import event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.user import UsersMethods

PASSWORD = "test-password"
HASHER = PasswordHasher()


def _post_user_form(client: FlaskClient, route: str, data: dict[str, str]) -> None:
    with client.application.test_request_context(base_url="https://localhost"):
        csrf_token: str = generate_csrf()   # type: ignore
        raw_token = session["csrf_token"]
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["csrf_token"] = raw_token
    response = client.post(
        route, base_url="https://localhost", headers={"Referer": "https://localhost/"},
        data=data | {"csrf_token": csrf_token},
    )
    assert response.status_code == 302


def test_credentials_keep_the_submitted_password(
    app: Flask, db_session: Session, create_admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ne prehache pas la saisie avant de connaitre le format stocke."""
    with app.test_request_context(
        "/login", method="POST", data={"username": "admin", "password": PASSWORD}
    ), monkeypatch.context() as scoped_patch:
        scoped_patch.setattr(g, "db_session", db_session, raising=False)
        from flask import request   # pylint: disable=C0415

        user, identifier, password = UsersMethods.get_user_from_credentials(request)

    assert user is create_admin_user
    assert identifier == "admin"
    assert password == PASSWORD


def test_first_successful_login_migrates_legacy_hash(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Migre le SHA-256 uniquement apres verification correcte du mot de passe."""
    old_hash = create_admin_user.sha_mdp
    response = _submit_login(client, "/gestion-droits")
    db_session.expire_all()

    assert response.headers["Location"] == "/gestion-droits"
    assert create_admin_user.sha_mdp != old_hash
    assert create_admin_user.sha_mdp.startswith("$argon2id$")
    assert HASHER.verify(create_admin_user.sha_mdp, PASSWORD)
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert browser_session["id"] == create_admin_user.id


def test_wrong_legacy_password_does_not_migrate(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Conserve l'ancien hash et compte uniquement la mauvaise saisie."""
    old_hash = create_admin_user.sha_mdp
    _submit_login(client, "/", password="incorrect")
    db_session.expire_all()

    assert create_admin_user.sha_mdp == old_hash
    assert create_admin_user.false_test == 1
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert "id" not in browser_session


def test_argon2_login_preserves_current_hash(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Ne recalcule pas un hash Argon2id dont les parametres sont deja actuels."""
    current_hash = HASHER.hash(PASSWORD)
    create_admin_user.sha_mdp = current_hash
    create_admin_user.false_test = 2
    db_session.commit()

    response = _submit_login(client, "/gestion-droits")
    db_session.expire_all()

    assert response.headers["Location"] == "/gestion-droits"
    assert create_admin_user.sha_mdp == current_hash
    assert create_admin_user.false_test == 0


def test_argon2_wrong_password_is_rejected(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Refuse une mauvaise saisie sans modifier le hash Argon2id."""
    current_hash = HASHER.hash(PASSWORD)
    create_admin_user.sha_mdp = current_hash
    db_session.commit()

    _submit_login(client, "/", password="incorrect")
    db_session.expire_all()

    assert create_admin_user.sha_mdp == current_hash
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert "id" not in browser_session


def test_argon2_parameters_are_upgraded_after_success(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Renforce automatiquement les parametres obsoletes apres verification."""
    old_hash = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(PASSWORD)
    create_admin_user.sha_mdp = old_hash
    db_session.commit()

    response = _submit_login(client, "/gestion-droits")
    db_session.expire_all()

    assert response.headers["Location"] == "/gestion-droits"
    assert create_admin_user.sha_mdp != old_hash
    assert HASHER.verify(create_admin_user.sha_mdp, PASSWORD)
    assert not HASHER.check_needs_rehash(create_admin_user.sha_mdp)


@pytest.mark.parametrize("status", ("locked", "expired"))
def test_blocked_account_does_not_migrate(
    client: FlaskClient, db_session: Session, create_admin_user: User, status: str
) -> None:
    """Ne migre pas un compte verrouille ou expire meme avec le bon mot de passe."""
    old_hash = create_admin_user.sha_mdp
    create_admin_user.locked = status == "locked"
    create_admin_user.fin = date.today() - timedelta(days=1) if status == "expired" else None
    db_session.commit()

    response = _submit_login(client, "/")
    db_session.expire_all()

    assert response.status_code == 302
    assert create_admin_user.sha_mdp == old_hash
    assert create_admin_user.false_test == 0
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert "id" not in browser_session


def test_future_expiration_allows_migration(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Autorise un compte dont la date de fin n'est pas encore atteinte."""
    create_admin_user.fin = date.today() + timedelta(days=1)
    db_session.commit()

    response = _submit_login(client, "/gestion-droits")
    db_session.expire_all()

    assert response.headers["Location"] == "/gestion-droits"
    assert create_admin_user.sha_mdp.startswith("$argon2id$")


@pytest.mark.parametrize("stored_hash", ("", "invalid", "z" * 64, "$argon2id$invalid"))
def test_invalid_stored_hash_is_rejected(
    client: FlaskClient, db_session: Session, create_admin_user: User, stored_hash: str
) -> None:
    """Refuse proprement les formats inconnus ou corrompus."""
    create_admin_user.sha_mdp = stored_hash
    db_session.commit()

    response = _submit_login(client, "/")
    db_session.expire_all()

    assert response.status_code == 302
    assert create_admin_user.sha_mdp == stored_hash
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert "id" not in browser_session


def test_unknown_account_does_not_authenticate(client: FlaskClient) -> None:
    """Refuse un compte absent sans exposer d'erreur interne."""
    response = _submit_login(client, "/")

    assert response.status_code == 302
    assert "AttributeError" not in response.headers["Location"]
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert "id" not in browser_session


def test_migration_commit_failure_allows_login_and_safe_log(
    client: FlaskClient, db_session: Session, create_admin_user: User,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Autorise apres rollback, conserve le SHA-256 et journalise sans secret."""
    old_hash = create_admin_user.sha_mdp
    user_id = create_admin_user.id

    def fail_commit(database_session: Session) -> None:
        if any(type(obj).__name__ == 'AuthSession' for obj in database_session.new):
            return
        raise SQLAlchemyError(f"sensitive-write-details {PASSWORD} {old_hash}")

    event.listen(Session, "before_commit", fail_commit)
    try:
        with caplog.at_level(logging.WARNING):
            response = _submit_login(client, "/gestion-droits")
    finally:
        event.remove(Session, "before_commit", fail_commit)
    db_session.expire_all()

    assert response.headers["Location"] == "/gestion-droits"
    assert create_admin_user.sha_mdp == old_hash
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert browser_session["id"] == user_id
    assert "MIGR-AUTH" in caplog.text
    assert "SQLAlchemyError" in caplog.text
    assert PASSWORD not in caplog.text
    assert old_hash not in caplog.text
    assert "sensitive-write-details" not in caplog.text

    _submit_login(client, "/gestion-droits")
    db_session.expire_all()
    assert create_admin_user.sha_mdp.startswith("$argon2id$")


def test_new_account_uses_argon2(
    client: FlaskClient, db_session: Session, authenticated_session_data: dict[str, Any]
) -> None:
    """Cree directement les nouveaux comptes au format Argon2id."""
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session.update(authenticated_session_data)
    _post_user_form(client, "/ajout-utilisateurs", {
        "prenom": "Nouveau", "nom": "Compte", "mail": "new@test.invalid",
        "identifiant": "new-user", "mdp": "new-test-password", "habil_1": "1",
    })

    user = db_session.scalar(select(User).where(User.identifiant == "new-user"))
    assert user is not None
    assert user.sha_mdp.startswith("$argon2id$")
    assert HASHER.verify(user.sha_mdp, "new-test-password")


@pytest.mark.parametrize("route", ("/modif-utilisateurs", "/gestion-droits"))
def test_password_change_uses_argon2(
    client: FlaskClient, db_session: Session, create_test_user: User,
    authenticated_session_data: dict[str, Any], route: str,
) -> None:
    """Utilise Argon2id dans tous les formulaires de changement du mot de passe."""
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session.update(authenticated_session_data)
    _post_user_form(client, route, {
        "prenom": create_test_user.prenom, "nom": create_test_user.nom,
        "mail": create_test_user.mail, "identifiant": "jdupont",
        "mdp": "changed-test-password", "habil_1": "1",
    })
    db_session.expire_all()

    assert create_test_user.sha_mdp.startswith("$argon2id$")
    assert HASHER.verify(create_test_user.sha_mdp, "changed-test-password")


@pytest.mark.parametrize("route", ("/modif-utilisateurs", "/gestion-droits"))
@pytest.mark.parametrize("format_name", ("sha256", "argon2"))
def test_empty_password_preserves_existing_hash(
    client: FlaskClient, db_session: Session, create_test_user: User,
    authenticated_session_data: dict[str, Any], route: str, format_name: str,
) -> None:
    """Ne change pas le hash quand le champ mot de passe est laisse vide."""
    if format_name == "argon2":
        create_test_user.sha_mdp = HASHER.hash(PASSWORD)
        db_session.commit()
    old_hash = create_test_user.sha_mdp
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session.update(authenticated_session_data)
    _post_user_form(client, route, {
        "prenom": create_test_user.prenom, "nom": create_test_user.nom,
        "mail": create_test_user.mail, "identifiant": "jdupont", "mdp": "", "habil_1": "1",
    })
    db_session.expire_all()

    assert create_test_user.sha_mdp == old_hash
