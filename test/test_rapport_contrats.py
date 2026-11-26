"""Tests du rapport automatise, de son jeton et du controle au demarrage."""

import os
import subprocess
import sys
from importlib import import_module
from smtplib import SMTPException
from typing import Any
from unittest.mock import Mock, patch

import pytest
from flask.testing import FlaskClient
from sqlalchemy.exc import SQLAlchemyError

from app.config.config import ConfigMail
from app.models import Contract

REPORT_TOKEN = "test-only-report-token"
REPORT_EMAIL = "direction@peraudiere.com"


@pytest.fixture
def report_client(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> tuple[FlaskClient, Mock]:
    """Configure un jeton dedie et remplace uniquement l'envoi du rapport."""
    monkeypatch.setattr(ConfigMail, "API_MAIL_TOKEN", REPORT_TOKEN)
    sender = Mock()
    monkeypatch.setattr("app.application.envoi_contrats_renego", sender)
    return client, sender


@pytest.mark.parametrize(
    "token",
    (None, "", "incorrect", "test-only-session-secret", "incorrect-é")
)
def test_report_rejects_invalid_token(
    report_client: tuple[FlaskClient, Mock],    # pylint: disable=W0621
    token: str | None
) -> None:
    """Refuse les jetons absents, invalides et la cle de session sans envoi."""
    client, sender = report_client
    headers = {"X-API-TOKEN": token} if token is not None else {}

    response = client.post("/rapport-contrats", json={"email": REPORT_EMAIL}, headers=headers)

    assert response.status_code == 401
    assert response.is_json
    sender.assert_not_called()


def test_report_accepts_dedicated_token_without_csrf(
    report_client: tuple[FlaskClient, Mock],    # pylint: disable=W0621
) -> None:
    """Autorise l'automatisation sans session ni jeton CSRF."""
    client, sender = report_client

    response = client.post(
        "/rapport-contrats", json={"email": REPORT_EMAIL},
        headers={"X-API-TOKEN": REPORT_TOKEN},
    )

    assert response.status_code == 200
    assert response.is_json
    sender.assert_called_once_with(REPORT_EMAIL)


def test_authenticated_session_does_not_replace_report_token(
    report_client: tuple[FlaskClient, Mock],    # pylint: disable=W0621
    authenticated_session_data: dict[str, Any],
) -> None:
    """Exige le jeton meme pour un administrateur deja connecte."""
    client, sender = report_client
    with client.session_transaction(base_url="https://localhost") as user_session:
        user_session.update(authenticated_session_data)

    response = client.post(
        "/rapport-contrats", json={"email": REPORT_EMAIL}, base_url="https://localhost"
    )

    assert response.status_code == 401
    sender.assert_not_called()


@pytest.mark.parametrize("error", (
    ValueError("internal-test-error"), OSError("internal-test-error"),
    SQLAlchemyError("internal-test-error"), SMTPException("internal-test-error"),
))
def test_report_errors_return_500_without_details(
    report_client: tuple[FlaskClient, Mock],    # pylint: disable=W0621
    error: Exception,
) -> None:
    """Ne transforme pas un echec en succes HTTP et ne divulgue pas l'exception."""
    client, sender = report_client
    sender.side_effect = error

    response = client.post(
        "/rapport-contrats", json={"email": REPORT_EMAIL},
        headers={"X-API-TOKEN": REPORT_TOKEN},
    )

    assert response.status_code == 500
    assert response.is_json
    assert b"internal-test-error" not in response.data


def test_csrf_remains_enabled_for_login(client: FlaskClient) -> None:
    """Reaffiche le formulaire quand le jeton CSRF du login est absent."""
    response = client.post("/login", data={"username": "admin", "password": "test-password"})

    assert response.status_code == 400
    page = response.get_data(as_text=True)
    assert 'name="csrf_token"' in page
    assert "La vérification de sécurité a échoué" in page


def test_real_report_generation_sends_email(
    client: FlaskClient, create_multiple_contracts: list[Contract]
) -> None:
    """Genere le vrai rapport depuis MariaDB et simule uniquement SMTP."""
    assert create_multiple_contracts
    with patch("smtplib.SMTP") as smtp:
        response = client.post(
            "/rapport-contrats", json={"email": REPORT_EMAIL},
            headers={"X-API-TOKEN": REPORT_TOKEN},
        )

        assert response.status_code == 200
        smtp.return_value.__enter__.return_value.send_message.assert_called_once()


def test_real_report_generation_propagates_smtp_failure(
    client: FlaskClient, create_multiple_contracts: list[Contract]
) -> None:
    """Ne masque pas une panne SMTP dans le veritable generateur de rapport."""
    assert create_multiple_contracts
    with patch("smtplib.SMTP", side_effect=SMTPException("internal-test-error")):
        response = client.post(
            "/rapport-contrats", json={"email": REPORT_EMAIL},
            headers={"X-API-TOKEN": REPORT_TOKEN},
        )

        assert response.status_code == 500
        assert b"internal-test-error" not in response.data


@pytest.mark.parametrize("token", ("", " \t"))
def test_missing_configuration_sends_alert_and_fails(
    monkeypatch: pytest.MonkeyPatch, token: str
) -> None:
    """Alerte le destinataire technique puis refuse une configuration sans jeton."""
    monkeypatch.setattr(ConfigMail, "API_MAIL_TOKEN", token)
    monkeypatch.setattr(ConfigMail, "EMAIL_USER", "intranet@test.invalid")
    reporting = import_module("app.rapport_echeances")

    with patch("smtplib.SMTP") as smtp:
        with pytest.raises(RuntimeError, match="API_MAIL_TOKEN"):
            reporting.validate_report_configuration()

        message = smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        assert message["To"] == "rverschuur@audit-io.fr"
        assert "rapport" in str(message).lower()


def test_alert_failure_does_not_allow_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse le demarrage meme si le serveur SMTP de l'alerte est indisponible."""
    monkeypatch.setattr(ConfigMail, "API_MAIL_TOKEN", "")
    reporting = import_module("app.rapport_echeances")

    with patch("smtplib.SMTP", side_effect=SMTPException("internal-test-error")):
        with pytest.raises(RuntimeError, match="API_MAIL_TOKEN"):
            reporting.validate_report_configuration()


def test_valid_configuration_does_not_send_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    """Accepte un jeton dedie sans envoyer d'alerte."""
    monkeypatch.setattr(ConfigMail, "API_MAIL_TOKEN", REPORT_TOKEN)
    reporting = import_module("app.rapport_echeances")

    with patch("smtplib.SMTP") as smtp:
        reporting.validate_report_configuration()

        smtp.assert_not_called()


def test_application_import_refuses_missing_token() -> None:
    """Verifie le vrai point d'entree dans un processus sans jeton configure."""
    program = """
from importlib import import_module
from unittest.mock import patch

with patch('smtplib.SMTP') as smtp:
    try:
        import_module('app.application')
    except RuntimeError as error:
        assert 'API_MAIL_TOKEN' in str(error)
        smtp.return_value.__enter__.return_value.send_message.assert_called_once()
    else:
        raise AssertionError('Le demarrage sans jeton aurait du echouer.')
"""
    result = subprocess.run(
        [sys.executable, "-c", program],
        env=os.environ | {"API_MAIL_TOKEN": ""},
        capture_output=True, text=True, check=False, timeout=20,
    )

    assert result.returncode == 0, result.stderr
