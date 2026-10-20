"""Tests des sessions persistantes et de leur revocation sur MariaDB reelle."""

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from importlib import import_module
from typing import Any
from urllib.parse import urlsplit
from test.test_login_redirects import _submit_login # type: ignore

import pytest
from flask import session
from flask.testing import FlaskClient
from flask_wtf.csrf import generate_csrf    # type: ignore
from sqlalchemy import event, inspect, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import ORMExecuteState, Session

from app.models import User


def _rows(db_session: Session) -> list[Any]:
    model = getattr(import_module("app.models"), "AuthSession")
    return list(db_session.scalars(select(model)).all())


def _token(client: FlaskClient) -> str:
    with client.session_transaction(base_url="https://localhost") as browser_session:
        return browser_session["auth_token"]


def _post(client: FlaskClient, route: str, data: dict[str, str]) -> Any:
    with client.application.test_request_context(base_url="https://localhost"):
        csrf_token: str = generate_csrf()   # type: ignore
        raw_token = session["csrf_token"]
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["csrf_token"] = raw_token
    return client.post(
        route, base_url="https://localhost", headers={"Referer": "https://localhost/"},
        data=data | {"csrf_token": csrf_token},
    )


def test_session_table_is_created_by_migration(db_session: Session) -> None:
    """Verifie le schema reel cree par la migration, pas par create_all."""
    inspector = inspect(db_session.connection())
    assert inspector.has_table("98_sessions")
    columns = {column["name"] for column in inspector.get_columns("98_sessions")}
    assert columns == {"token_hash", "id_user", "created_at", "last_seen_at", "expires_at"}
    foreign_keys = inspector.get_foreign_keys("98_sessions")
    assert foreign_keys[0]["referred_table"] == "99_users"
    assert {index["name"] for index in inspector.get_indexes("98_sessions")} >= {
        "ix_98_sessions_id_user", "ix_98_sessions_expires_at",
    }


def test_login_persists_only_token_fingerprint(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Ne stocke pas le jeton de navigateur en clair dans la base."""
    assert _submit_login(client, "/").status_code == 302
    token = _token(client)
    rows = _rows(db_session)

    assert len(token) >= 40
    assert len(rows) == 1
    assert rows[0].token_hash == sha256(token.encode()).hexdigest()
    assert rows[0].token_hash != token
    assert rows[0].id_user == create_admin_user.id
    assert timedelta(minutes=19, seconds=59) <= rows[0].expires_at - rows[0].created_at \
        <= timedelta(minutes=20, seconds=1)


def test_legacy_identity_cookie_is_not_authentication(client: FlaskClient) -> None:
    """N'accepte plus les anciennes informations de session sans ligne en base."""
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session.update(id=1, prenom="Admin", nom="Test", habilitation="1")

    response = client.get("/", base_url="https://localhost")

    assert response.status_code == 302
    assert urlsplit(response.headers["Location"]).path == "/login"


def test_active_session_refreshes_inactivity_deadline(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Renouvelle l'expiration apres une requete authentifiee."""
    assert create_admin_user.identifiant == "admin"
    _submit_login(client, "/")
    row = _rows(db_session)[0]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row.last_seen_at = now - timedelta(minutes=10)
    row.expires_at = now + timedelta(minutes=10)
    db_session.commit()
    previous_expiration = row.expires_at

    response = client.get("/", base_url="https://localhost")
    db_session.expire_all()

    assert response.status_code == 200
    assert row.expires_at > previous_expiration + timedelta(minutes=9)


def test_expired_session_is_rejected_and_removed(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Refuse une session meme si le cookie du navigateur existe encore."""
    assert create_admin_user.identifiant == "admin"
    _submit_login(client, "/")
    _rows(db_session)[0].expires_at = datetime.now(timezone.utc) \
        .replace(tzinfo=None) - timedelta(seconds=1)
    db_session.commit()

    response = client.get("/", base_url="https://localhost")

    assert response.status_code == 302
    assert urlsplit(response.headers["Location"]).path == "/login"
    assert not _rows(db_session)
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert "auth_token" not in browser_session


def test_logout_revokes_only_current_browser(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Conserve une autre connexion du meme compte lors d'une deconnexion."""
    assert create_admin_user.identifiant == "admin"
    second = client.application.test_client()
    _submit_login(client, "/")
    _submit_login(second, "/")
    old_token = _token(client)

    response = client.get("/logout", base_url="https://localhost")

    assert response.status_code == 302
    assert len(_rows(db_session)) == 1
    assert second.get("/", base_url="https://localhost").status_code == 200
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["auth_token"] = old_token
    assert client.get("/", base_url="https://localhost").status_code == 302


@pytest.mark.parametrize("route", ("/modif-utilisateurs", "/gestion-droits"))
@pytest.mark.parametrize("change", ("password", "permissions"))
def test_sensitive_change_revokes_all_browsers(
    client: FlaskClient, db_session: Session, create_admin_user: User, route: str, change: str
) -> None:
    """Revoque toutes les sessions, y compris celle qui modifie son propre compte."""
    second = client.application.test_client()
    _submit_login(client, "/")
    _submit_login(second, "/")
    response = _post(client, route, {
        "identifiant": "admin", "prenom": create_admin_user.prenom,
        "nom": create_admin_user.nom, "mail": create_admin_user.mail,
        "mdp": "changed-test-password" if change == "password" else "",
        "habil_1": "2" if change == "permissions" else "1",
    })

    assert response.status_code == 302
    assert not _rows(db_session)
    for browser in (client, second):
        response = browser.get("/", base_url="https://localhost")
        assert response.status_code == 302
        assert urlsplit(response.headers["Location"]).path == "/login"


@pytest.mark.parametrize("status", ("locked", "expired", "not-started"))
def test_account_state_is_checked_on_each_request(
    client: FlaskClient, db_session: Session, create_admin_user: User, status: str
) -> None:
    """Relit l'etat courant du compte, sans se fier aux informations du cookie."""
    _submit_login(client, "/")
    create_admin_user.locked = status == "locked"
    create_admin_user.fin = date.today() if status == "expired" else None
    create_admin_user.debut = date.today() + timedelta(days=1) \
        if status == "not-started" \
        else date.today()
    db_session.commit()

    response = client.get("/", base_url="https://localhost")

    assert response.status_code == 302
    assert urlsplit(response.headers["Location"]).path == "/login"


def test_request_uses_database_permissions_not_cookie(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Ne permet pas au cookie de conserver une habilitation absente en base."""
    _submit_login(client, "/")
    create_admin_user.habilitation = 2
    db_session.commit()
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["habilitation"] = "1"

    response = client.get("/gestion-droits", base_url="https://localhost")

    assert response.status_code != 200


def test_session_creation_failure_refuses_login(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """N'ouvre pas de session de navigateur si la ligne ne peut pas etre enregistree."""
    assert create_admin_user.identifiant == "admin"

    def fail_session_write(database_session: Session, _flush_context: Any, _instances: Any) -> None:
        if any(type(obj).__name__ == "AuthSession" for obj in database_session.new):
            raise SQLAlchemyError("test-only-session-write-failure")

    event.listen(Session, "before_flush", fail_session_write)
    try:
        response = _submit_login(client, "/")
    finally:
        event.remove(Session, "before_flush", fail_session_write)

    assert response.status_code == 503
    assert not _rows(db_session)
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert "auth_token" not in browser_session
        assert "id" not in browser_session


def test_sensitive_change_rollback_preserves_sessions(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Ne revoque pas des sessions si la modification du compte est annulee."""
    _submit_login(client, "/")

    def fail_user_write(
            database_session: Session,
            flush_context: Any, # pylint: disable=W0613
            instances: Any, # pylint: disable=W0613
        ) -> None:
        if any(isinstance(obj, User) for obj in database_session.dirty):
            raise SQLAlchemyError("test-only-user-write-failure")

    event.listen(Session, "before_flush", fail_user_write)
    try:
        response = _post(
            client,
            "/gestion-droits",
            {
                "identifiant": "admin",
                "mdp": "",
                "habil_1": "2",
            },
        )
    finally:
        event.remove(Session, "before_flush", fail_user_write)
    db_session.expire_all()

    assert response.status_code == 503
    assert create_admin_user.habilitation == 1
    assert len(_rows(db_session)) == 1
    assert client.get("/", base_url="https://localhost").status_code == 200


def test_session_lookup_failure_refuses_protected_access(
    client: FlaskClient, create_admin_user: User
) -> None:
    """Refuse l'acces si la verification en base est indisponible."""
    assert create_admin_user.identifiant == "admin"
    _submit_login(client, "/")

    def fail_session_lookup(state: ORMExecuteState) -> None:
        if state.is_select and state.bind_mapper is not None \
                and state.bind_mapper.class_.__name__ == 'AuthSession':
            raise SQLAlchemyError('test-only-session-read-failure')

    event.listen(Session, 'do_orm_execute', fail_session_lookup)
    try:
        response = client.get('/gestion-droits', base_url='https://localhost')
    finally:
        event.remove(Session, 'do_orm_execute', fail_session_lookup)

    assert response.status_code == 503
    assert b'test-only-session-read-failure' not in response.data
    with client.session_transaction(base_url='https://localhost') as browser_session:
        assert 'auth_token' not in browser_session


def test_new_login_rotates_current_browser_token(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """Remplace le jeton d'un navigateur au lieu de reutiliser sa connexion."""
    assert create_admin_user.identifiant == 'admin'
    _submit_login(client, '/')
    old_token = _token(client)

    _submit_login(client, '/')

    assert _token(client) != old_token
    assert len(_rows(db_session)) == 1


def test_deleted_account_cannot_keep_access(
    client: FlaskClient, db_session: Session, create_admin_user: User
) -> None:
    """La suppression d'un compte invalide aussi la session du navigateur."""
    _submit_login(client, '/')
    db_session.delete(create_admin_user)
    db_session.commit()

    response = client.get('/', base_url='https://localhost')

    assert response.status_code == 302
    assert urlsplit(response.headers['Location']).path == '/login'
    assert not _rows(db_session)
