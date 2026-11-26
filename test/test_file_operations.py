"""Tests des opérations de fichiers utilisées par les contrats."""

import json
import subprocess
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pytest
from flask import Flask, session
from flask.testing import FlaskClient
from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage

from app.config.config import ConfigApp
from app.docs import download_file, exchange_files, print_document
from app.impression import DEFAULT_PRINTER_IP, print_file
from app.models import Bill, DocToSigne, Document, Points, User
from app.repositories.auth_session import create_auth_session
from app.signatures import SecureDocumentAccess


@pytest.mark.parametrize("model", (Document, Bill))
def test_model_upload_propagates_filesystem_errors(
    monkeypatch: pytest.MonkeyPatch,
    model: type[Document] | type[Bill],
) -> None:
    """L’échec disque doit remonter au contrôleur pour déclencher son rollback."""
    monkeypatch.setattr("app.docs.upload_file", Mock(side_effect=OSError("disk full")))
    record = model(str_lien="document-test.pdf")
    uploaded_file = FileStorage(BytesIO(b"document"), filename="source.pdf")

    with pytest.raises(OSError, match="disk full"):
        record.upload(file_to_upload=uploaded_file)


def test_failed_file_exchange_preserves_the_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un remplacement incomplet laisse l’ancien fichier intact."""
    monkeypatch.setattr(ConfigApp, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setattr("app.docs._folder_initialized", False)
    old_path = tmp_path / "old.pdf"
    old_path.write_bytes(b"original")

    class BrokenStream(BytesIO):
        """Flux de données qui échoue lors de la lecture."""
        def read(self, size: int | None = -1) -> bytes:
            raise OSError("upload interrupted")

    new_file = FileStorage(BrokenStream(), filename="new.pdf")

    with pytest.raises(OSError, match="upload interrupted"):
        exchange_files("old.pdf", new_file, "new.pdf")

    assert old_path.read_bytes() == b"original"
    assert not (tmp_path / "new.pdf").exists()


def test_download_file_returns_not_found_for_missing_files(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Un fichier absent reste une réponse 404 explicite."""
    monkeypatch.setattr(ConfigApp, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setattr("app.docs._folder_initialized", False)

    with app.test_request_context("/"):
        response, status = download_file("missing.pdf") # type: ignore

    assert status == 404
    assert response.json["erreur"] == "Erreur de fichier introuvable : missing.pdf" # type: ignore


def test_download_file_does_not_swallow_unexpected_errors(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Une erreur de programmation n’est pas transformée en erreur de téléchargement."""
    monkeypatch.setattr(ConfigApp, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setattr("app.docs._folder_initialized", False)
    monkeypatch.setattr(
        "app.docs.secure_filename",
        Mock(side_effect=TypeError("invalid filename type")),
    )

    with app.test_request_context("/"):
        with pytest.raises(TypeError, match="invalid filename type"):
            download_file("document.pdf")


def test_temporary_access_is_bound_to_user_and_expiration(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """L’accès temporaire est isolé par utilisateur et disparaît à expiration."""
    temp_dir = tmp_path / "signature"
    monkeypatch.setattr(SecureDocumentAccess, "TEMP_DIR", str(temp_dir))

    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "192.0.2.1"}):
        session["identifiant"] = "alice"
        SecureDocumentAccess.create_temp_access_file("document.pdf", "valid-hash")
        assert SecureDocumentAccess.verify_temp_access("document.pdf") is True

        session["identifiant"] = "bob"
        assert SecureDocumentAccess.verify_temp_access("document.pdf") is False

        expired_path = temp_dir / "expired-hash.json"
        expired_path.write_text(
            json.dumps({
                "filename": "expired.pdf",
                "user_identifier": SecureDocumentAccess.get_user_identifier(),
                "expires_at": 0,
            }),
            encoding="utf-8",
        )
        corrupt_path = temp_dir / "corrupt-hash.json"
        corrupt_path.write_text("{invalid", encoding="utf-8")

        assert SecureDocumentAccess.verify_temp_access("expired.pdf") is False
        SecureDocumentAccess.cleanup_expired_temp_files()

    assert not expired_path.exists()
    assert not corrupt_path.exists()


def test_download_routes_allow_only_document_signatories(
    app: Flask,
    client: FlaskClient,
    db_session: Session,
    create_admin_user: User,
    create_test_user: User,
    authenticated_session_data: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Les téléchargements temporaires et définitifs sont réservés au signataire."""
    temp_dir = tmp_path / "signature"
    temp_dir.mkdir()
    monkeypatch.setattr(SecureDocumentAccess, "TEMP_DIR", str(temp_dir))
    final_path = tmp_path / "signed" / "signed.pdf"
    final_path.parent.mkdir()
    final_path.write_bytes(b"signed-pdf")
    document = DocToSigne(
        doc_nom="signed.pdf",
        doc_type="Contrat",
        echeance=3,
        duree_archivage=3660,
        chemin_fichier=str(final_path),
        hash_fichier="document-hash",
        id_user=create_admin_user.id,
    )
    db_session.add(document)
    db_session.flush()
    db_session.add(Points(
        id_document=document.id,
        x=1,
        y=1,
        page_num=1,
        id_user=create_admin_user.id,
    ))
    db_session.commit()

    user_agent = "file-access-test"
    with app.test_request_context(
        "/", headers={"User-Agent": user_agent}, environ_base={"REMOTE_ADDR": "127.0.0.1"}
    ):
        session["identifiant"] = create_admin_user.identifiant
        SecureDocumentAccess.create_temp_access_file("temporary.pdf", "temporary-hash")
    (temp_dir / "temporary.pdf").write_bytes(b"temporary-pdf")

    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session.update(authenticated_session_data)
    final_response = client.get(
        "/signature/download/signed.pdf", base_url="https://localhost"
    )
    temporary_response = client.get(
        "/signature/download/temporary.pdf?temp_dir=true",
        headers={"User-Agent": user_agent},
        base_url="https://localhost",
    )
    assert final_response.status_code == 200
    assert final_response.data == b"signed-pdf"
    assert temporary_response.status_code == 200
    assert temporary_response.data == b"temporary-pdf"

    other_token = create_auth_session(db_session, create_test_user.id)
    db_session.commit()
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["auth_token"] = other_token
    assert client.get(
        "/signature/download/signed.pdf", base_url="https://localhost"
    ).status_code == 403
    assert client.get(
        "/signature/download/temporary.pdf?temp_dir=true",
        headers={"User-Agent": user_agent},
        base_url="https://localhost",
    ).status_code == 403


def test_print_file_builds_cups_command_and_uses_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """La commande CUPS contient les options attendues et le serveur de repli."""
    run = Mock(return_value=subprocess.CompletedProcess([], 0, stdout="job-42", stderr=""))
    monkeypatch.setattr("app.impression.get_cups_server", lambda: DEFAULT_PRINTER_IP)
    monkeypatch.setattr("app.impression.get_printer_name", lambda: "test-printer")
    monkeypatch.setattr("app.impression.subprocess.run", run)
    file_path = tmp_path / "print.pdf"
    file_path.write_bytes(b"pdf")

    print_file(
        str(file_path),
        user_name="Test User",
        site_name="Intranet",
        copies="2",
        sides="two-sided-long-edge",
        media="A4",
        orientation="4",
        color="color",
    )

    command = run.call_args.args[0]
    assert command[:4] == ["lp", "-d", "test-printer", "-n"]
    assert "2" in command
    assert "PageSize=A4" in command
    assert "Duplex=DuplexNoTumble" in command
    assert "landscape" in command
    assert "ColorModel=RGB" in command
    assert run.call_args.kwargs["env"]["CUPS_SERVER"] == DEFAULT_PRINTER_IP


@pytest.mark.parametrize(
    "failure",
    (subprocess.TimeoutExpired("lp", 30), FileNotFoundError("lp")),
)
def test_print_file_translates_system_failures(
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
) -> None:
    """Le timeout et l’absence de lp remontent comme erreurs d’impression."""
    monkeypatch.setattr("app.impression.get_cups_server", lambda: DEFAULT_PRINTER_IP)
    monkeypatch.setattr("app.impression.get_printer_name", lambda: "test-printer")
    monkeypatch.setattr("app.impression.subprocess.run", Mock(side_effect=failure))

    with pytest.raises(RuntimeError, match="Timeout|Commande lp"):
        print_file("document.pdf")


def test_print_document_removes_spool_after_failure(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Le fichier de spool est supprimé même si l’envoi à CUPS échoue."""
    print_dir = tmp_path / "print"
    print_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(ConfigApp, "PRINT_PATH", str(print_dir))
    monkeypatch.setattr("app.docs.print_file", Mock(side_effect=RuntimeError("printer offline")))

    with app.test_request_context("/"):
        response = print_document(
            BytesIO(b"print-content"), "job", "pdf", "1", "tester",
            "one-sided", "A4", "3", "monochrome",
        )

    assert response.json["erreur"]  # type: ignore
    assert list(print_dir.iterdir()) == []  # pylint: disable=C1803
