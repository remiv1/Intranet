"""Tests des destinations locales apres une tentative de connexion."""

import re
from urllib.parse import parse_qs, urlsplit

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app.models import User
from app.repositories.user import UsersMethods

LOCAL_DESTINATIONS = (
    "/", "/contrats/", "/contrats/?tab=documents&recherche=a%20b",
    "/contrats/?retour=https%3A%2F%2Fexample.invalid#documents",
)
INVALID_DESTINATIONS = (
    None, "", "None", "contrats/", "https://example.invalid/",
    "https://localhost/contrats/", "//example.invalid/", "///example.invalid/",
    "javascript:alert(1)", "/\\example.invalid/", "/%5cexample.invalid/",
    "/%2fexample.invalid/", "/%252fexample.invalid/", "/%255cexample.invalid/",
    "\n//example.invalid/", "/\r\nLocation: https://example.invalid/",
    "/%0d%0aLocation:external", "/%09/evil", "/\x7f/evil",
)


def _submit_login(
    client: FlaskClient, destination: str, password: str = "test-password"
) -> TestResponse:
    login_page = client.get("/login", base_url="https://localhost")
    token_match = re.search(
        r'name="csrf_token"[^>]*value="([^"]+)"',
        login_page.get_data(as_text=True),
    )
    assert login_page.status_code == 200
    assert token_match is not None
    return client.post(
        "/login", base_url="https://localhost",
        headers={"Referer": "https://localhost/login"},
        data={
            "username": "admin", "password": password,
            "preview_request": destination, "csrf_token": token_match.group(1),
        },
    )


@pytest.mark.parametrize("destination", LOCAL_DESTINATIONS)
def test_success_keeps_local_destination(app: Flask, destination: str) -> None:
    """Conserve le chemin local, les parametres et le fragment sans les modifier."""
    with app.test_request_context(base_url="https://localhost"):
        response = UsersMethods.handle_login_redirect(destination, success=True)

    assert response.status_code == 302
    assert response.headers["Location"] == destination


@pytest.mark.parametrize("destination", INVALID_DESTINATIONS)
def test_success_falls_back_to_home(app: Flask, destination: str | None) -> None:
    """Revient a l'accueil si la destination n'est pas un chemin local sur."""
    with app.test_request_context(base_url="https://localhost"):
        response = UsersMethods.handle_login_redirect(destination, success=True)

    location = urlsplit(response.headers["Location"])   # type: ignore
    assert response.status_code == 302
    assert location.scheme == ""   # type: ignore
    assert location.netloc == ""   # type: ignore
    assert location.path == "/"   # type: ignore


@pytest.mark.parametrize("destination", LOCAL_DESTINATIONS)
def test_failure_preserves_local_destination(app: Flask, destination: str) -> None:
    """Conserve la destination locale pour la prochaine tentative."""
    with app.test_request_context(base_url="https://localhost"):
        response = UsersMethods.handle_login_redirect(
            destination,
            error_message="Connexion refusee",
        )

    location = urlsplit(response.headers["Location"])   # type: ignore
    assert location.path == "/login"   # type: ignore
    assert parse_qs(location.query)["preview_request"] == [destination]   # type: ignore


@pytest.mark.parametrize("destination", INVALID_DESTINATIONS)
def test_failure_discards_invalid_destination(app: Flask, destination: str | None) -> None:
    """Ne retransmet pas une destination dangereuse dans le formulaire suivant."""
    with app.test_request_context(base_url="https://localhost"):
        response = UsersMethods.handle_login_redirect(
            destination,
            error_message="Connexion refusee",
        )

    location = urlsplit(response.headers["Location"])   # type: ignore
    assert location.path == "/login"   # type: ignore
    assert "preview_request" not in parse_qs(
        location.query,   # type: ignore
        keep_blank_values=True,
    )


def test_protected_get_captures_relative_path(client: FlaskClient) -> None:
    """Ne recopie pas l'hote de la requete dans la destination apres connexion."""
    response = client.get(
        "/gestion-droits?tab=users&recherche=a%20b", base_url="https://localhost"
    )

    location = urlsplit(response.headers["Location"])
    assert location.path == "/login"
    destination = parse_qs(location.query)["preview_request"][0]
    assert destination.startswith("/gestion-droits?")
    assert urlsplit(destination).scheme == ""
    assert urlsplit(destination).netloc == ""
    assert parse_qs(urlsplit(destination).query) == {"tab": ["users"], "recherche": ["a b"]}


def test_real_login_redirects_to_local_destination(
    client: FlaskClient, create_admin_user: User
) -> None:
    """Authentifie le compte MariaDB avec CSRF actif puis suit une destination locale."""
    response = _submit_login(client, "/gestion-droits?tab=users")

    assert response.status_code == 302
    assert response.headers["Location"] == "/gestion-droits?tab=users"
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert browser_session["id"] == create_admin_user.id


def test_real_login_ignores_external_destination(
    client: FlaskClient, create_admin_user: User
) -> None:
    """Conserve la connexion reussie tout en refusant de quitter l'intranet."""
    response = _submit_login(client, "https://example.invalid/")

    assert response.status_code == 302
    location = urlsplit(response.headers["Location"])
    assert location.scheme == ""
    assert location.netloc == ""
    assert location.path == "/"
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert browser_session["id"] == create_admin_user.id


def test_real_login_failure_keeps_local_destination(
    client: FlaskClient, create_admin_user: User
) -> None:
    """Conserve le chemin apres un mauvais mot de passe sans ouvrir de session."""
    assert create_admin_user.identifiant == "admin"
    response = _submit_login(client, "/gestion-droits?tab=users", password="incorrect")

    location = urlsplit(response.headers["Location"])
    assert response.status_code == 302
    assert location.path == "/login"
    assert parse_qs(location.query)["preview_request"] == ["/gestion-droits?tab=users"]
    with client.session_transaction(base_url="https://localhost") as browser_session:
        assert "id" not in browser_session


def test_real_login_failure_discards_external_destination(
    client: FlaskClient, create_admin_user: User
) -> None:
    """Ecarte la destination externe meme lorsque les identifiants sont incorrects."""
    assert create_admin_user.identifiant == "admin"
    response = _submit_login(client, "//example.invalid/", password="incorrect")

    location = urlsplit(response.headers["Location"])
    assert location.path == "/login"
    assert "preview_request" not in parse_qs(location.query)


@pytest.mark.parametrize("csrf_token", ("invalid-token", ""))
def test_invalid_login_csrf_renders_french_error(
    client: FlaskClient, csrf_token: str
) -> None:
    """Reaffiche le formulaire en francais pour un jeton CSRF invalide."""
    response = client.post(
        "/login", base_url="https://localhost",
        data={
            "username": "admin", "password": "test-password",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 400
    page = response.get_data(as_text=True)
    assert 'name="csrf_token"' in page
    assert "La vérification de sécurité a échoué" in page


def test_expired_login_csrf_renders_french_error(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reaffiche le formulaire en francais lorsque le jeton CSRF a expire."""
    login_page = client.get("/login", base_url="https://localhost")
    token_match = re.search(
        r'name="csrf_token"[^>]*value="([^"]+)"',
        login_page.get_data(as_text=True),
    )
    assert token_match is not None
    monkeypatch.setitem(client.application.config, "WTF_CSRF_TIME_LIMIT", -1)

    response = client.post(
        "/login", base_url="https://localhost",
        data={
            "username": "admin", "password": "test-password",
            "csrf_token": token_match.group(1),
        },
    )

    assert response.status_code == 400
    page = response.get_data(as_text=True)
    assert 'name="csrf_token"' in page
    assert "La vérification de sécurité a échoué" in page
