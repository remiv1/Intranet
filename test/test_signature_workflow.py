"""Tests du parcours de signature électronique."""

from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any
from collections.abc import Callable
from unittest.mock import Mock

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import DocToSigne, Invitation, Points, Signatures, User
from app.repositories.auth_session import create_auth_session
from app.signatures import SecureDocumentAccess


@pytest.fixture
def signature_flow(
    app: Flask,
    client: FlaskClient,
    db_session: Session,
    create_admin_user: User,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Any]:
    """Crée un document, son signataire, son invitation et une session valide."""
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    pdf_path = tmp_path / "document.pdf"
    pdf_content = b"pdf-test-signature"
    pdf_path.write_bytes(pdf_content)
    document = DocToSigne(
        doc_nom="document.pdf",
        doc_type="Contrat",
        doc_sous_type="Test",
        echeance=3,
        duree_archivage=3660,
        chemin_fichier=str(pdf_path),
        hash_fichier=sha256(pdf_content).hexdigest(),
        id_user=create_admin_user.id,
    )
    db_session.add(document)
    db_session.flush()
    point = Points(
        id_document=document.id,
        x=10,
        y=20,
        page_num=1,
        id_user=create_admin_user.id,
    )
    invitation = Invitation(
        id_document=document.id,
        id_user=create_admin_user.id,
        token="valid-invitation-token",
        expire_at=datetime.now() + timedelta(days=1),
        code_otp="123456",
    )
    second_signer = User(
        prenom="Sophie",
        nom="Signer",
        mail="signer2@test.invalid",
        identifiant="signer2",
        sha_mdp=sha256(b"test-password").hexdigest(),
        habilitation=5,
        false_test=0,
        locked=False,
    )
    db_session.add(second_signer)
    db_session.add_all((point, invitation))
    auth_token = create_auth_session(db_session, create_admin_user.id)
    db_session.commit()

    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["auth_token"] = auth_token

    return {
        "document": document,
        "invitation": invitation,
        "point": point,
        "second_signer": second_signer,
        "user": create_admin_user,
    }


def test_signature_rejects_wrong_invitation_token_without_mutation(
    client: FlaskClient,
    db_session: Session,
    signature_flow: dict[str, Any], # pylint: disable=W0621
) -> None:
    """Refuse un jeton invalide sans créer de signature ni signer le point."""
    document = signature_flow["document"]
    point = signature_flow["point"]

    response = client.post(
        f"/signature/signer/{document.id}/{document.hash_fichier}",
        json={"otp_code": "123456", "signature_hash": "signature-test"},
        headers={"X-Invit-Token": "wrong-token"},
        base_url="https://localhost",
    )

    db_session.refresh(point)
    assert response.status_code == 400
    assert point.status == 0
    assert db_session.scalars(select(Signatures)).all() == []


@pytest.mark.parametrize(
    ("otp", "token"),
    (("000000", "valid-invitation-token"), ("123456", "wrong-token")),
)
def test_signature_rejects_invalid_otp_or_invitation_token(
    client: FlaskClient,
    db_session: Session,
    signature_flow: dict[str, Any], # pylint: disable=W0621
    otp: str,
    token: str,
) -> None:
    """Refuse un OTP ou un jeton invalide sans enregistrer de signature."""
    document = signature_flow["document"]
    point = signature_flow["point"]

    response = client.post(
        f"/signature/signer/{document.id}/{document.hash_fichier}",
        json={"otp_code": otp, "signature_hash": "signature-test"},
        headers={"X-Invit-Token": token},
        base_url="https://localhost",
    )

    db_session.refresh(point)
    assert response.status_code == 400
    assert point.status == 0
    assert db_session.scalars(select(Signatures)).all() == []


def test_signature_rejects_expired_invitation(
    client: FlaskClient,
    db_session: Session,
    signature_flow: dict[str, Any], # pylint: disable=W0621
) -> None:
    """Refuse une invitation expirée même si son jeton et son OTP sont corrects."""
    document = signature_flow["document"]
    invitation = signature_flow["invitation"]
    point = signature_flow["point"]
    invitation.expire_at = datetime.now() - timedelta(seconds=1)
    db_session.commit()

    response = client.post(
        f"/signature/signer/{document.id}/{document.hash_fichier}",
        json={"otp_code": "123456", "signature_hash": "signature-test"},
        headers={"X-Invit-Token": invitation.token},
        base_url="https://localhost",
    )

    db_session.refresh(point)
    assert response.status_code == 400
    assert point.status == 0
    assert db_session.scalars(select(Signatures)).all() == []


def test_signature_can_only_be_submitted_once(
    client: FlaskClient,
    db_session: Session,
    signature_flow: dict[str, Any], # pylint: disable=W0621
) -> None:
    """Le rejeu d'une signature déjà validée est refusé sans seconde ligne."""
    document = signature_flow["document"]
    invitation = signature_flow["invitation"]
    point = signature_flow["point"]
    request_data: dict[str, Any] = {
        "json": {"otp_code": "123456", "signature_hash": "signature-test"},
        "headers": {"X-Invit-Token": invitation.token},
        "base_url": "https://localhost",
    }

    first_response = client.post(
        f"/signature/signer/{document.id}/{document.hash_fichier}", **request_data
    )
    replay_response = client.post(
        f"/signature/signer/{document.id}/{document.hash_fichier}", **request_data
    )

    db_session.refresh(point)
    assert first_response.status_code == 200
    assert replay_response.status_code == 400
    assert point.status == 1
    assert len(db_session.scalars(select(Signatures)).all()) == 1


def test_multi_signer_document_is_complete_only_after_both_signatures(
    client: FlaskClient,
    db_session: Session,
    signature_flow: dict[str, Any], # pylint: disable=W0621
) -> None:
    """Le document reste en attente après la première signature, puis est complété."""
    document = signature_flow["document"]
    second_signer = signature_flow["second_signer"]
    second_point = Points(
        id_document=document.id,
        x=30,
        y=40,
        page_num=1,
        id_user=second_signer.id,
    )
    second_invitation = Invitation(
        id_document=document.id,
        id_user=second_signer.id,
        token="second-invitation-token",
        expire_at=datetime.now() + timedelta(days=1),
        code_otp="654321",
    )
    db_session.add_all((second_point, second_invitation))
    db_session.commit()

    first_response = client.post(
        f"/signature/signer/{document.id}/{document.hash_fichier}",
        json={"otp_code": "123456", "signature_hash": "first-signature"},
        headers={"X-Invit-Token": signature_flow["invitation"].token},
        base_url="https://localhost",
    )
    assert first_response.status_code == 200
    assert first_response.json["all_signed"] is False   # type: ignore

    second_auth_token = create_auth_session(db_session, second_signer.id)
    db_session.commit()
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["auth_token"] = second_auth_token

    second_response = client.post(
        f"/signature/signer/{document.id}/{document.hash_fichier}",
        json={"otp_code": "654321", "signature_hash": "second-signature"},
        headers={"X-Invit-Token": second_invitation.token},
        base_url="https://localhost",
    )

    db_session.refresh(document)
    assert second_response.status_code == 200
    assert second_response.json["all_signed"] is True   # type: ignore
    assert document.status == 1
    assert len(db_session.scalars(select(Signatures)).all()) == 2


@pytest.mark.parametrize("file_state", ("missing", "modified"))
def test_finalization_rejects_missing_or_modified_pdf(
    client: FlaskClient,
    signature_flow: dict[str, Any], # pylint: disable=W0621
    file_state: str,
) -> None:
    """La finalisation vérifie l’existence et l’empreinte avant le traitement PDF."""
    document = signature_flow["document"]
    pdf_path = Path(document.chemin_fichier)
    if file_state == "missing":
        pdf_path.unlink()
    else:
        pdf_path.write_bytes(b"modified-pdf")

    response = client.post(
        f"/signature/creer/{document.id}/{document.hash_fichier}",
        base_url="https://localhost",
    )

    assert response.status_code == (404 if file_state == "missing" else 400)


def test_finalization_rejects_unsigned_points(
    client: FlaskClient,
    signature_flow: dict[str, Any], # pylint: disable=W0621
) -> None:
    """La génération du PDF final est refusée tant qu’un point reste à signer."""
    document = signature_flow["document"]

    response = client.post(
        f"/signature/creer/{document.id}/{document.hash_fichier}",
        base_url="https://localhost",
    )

    assert response.status_code == 400
    assert b"Signatures manquantes" in response.data


@pytest.mark.parametrize("failure", ("invitation", "commit"))
def test_signature_upload_failure_rolls_back_and_restores_temporary_pdf(
    app: Flask,
    client: FlaskClient,
    db_session: Session,
    create_admin_user: User,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: str,
) -> None:
    """Un échec d’invitation ou de commit restaure le PDF et annule les lignes créées."""
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    temp_dir = tmp_path / "temporary"
    temp_dir.mkdir()
    final_dir = tmp_path / "final"
    monkeypatch.setattr(SecureDocumentAccess, "TEMP_DIR", str(temp_dir))
    monkeypatch.setenv("SIGNATURE_DOCKER_PATH", str(final_dir))
    pdf_path = temp_dir / "upload.pdf"
    pdf_path.write_bytes(b"signature-pdf")

    auth_token = create_auth_session(db_session, create_admin_user.id)
    db_session.commit()
    with client.session_transaction(base_url="https://localhost") as browser_session:
        browser_session["auth_token"] = auth_token

    expected_error: type[Exception]
    fail_signature_commit: Callable[[Session], None] | None = None  # type: ignore
    if failure == "invitation":
        monkeypatch.setattr(
            "app.signatures.signature_maker.send_email_invitation",
            Mock(side_effect=RuntimeError("mail unavailable")),
        )
        expected_error = RuntimeError
        expected_message = "mail unavailable"
    else:
        monkeypatch.setattr(
            "app.signatures.signature_maker.send_email_invitation",
            Mock(return_value=None),
        )
        expected_error = SQLAlchemyError
        expected_message = "signature commit failed"

        def fail_signature_commit(database_session: Session) -> None:
            if any(isinstance(item, DocToSigne) for item in database_session.identity_map.values()):
                raise SQLAlchemyError(expected_message)

        event.listen(Session, "before_commit", fail_signature_commit)

    try:
        with pytest.raises(expected_error, match=expected_message):
            client.post(
                "/signature/deposer",
                data={
                    "doc_id": "upload.pdf",
                    "document_name": "upload.pdf",
                    "document_type": "Contrat",
                    "document_subtype": "Test",
                    "document_priority": "0",
                    "signing_deadline": "3",
                    "document_validity": "3660",
                    "document_description": "Signature rollback test",
                    "signature_points[0][x]": "10",
                    "signature_points[0][y]": "20",
                    "signature_points[0][pageNum]": "1",
                    "signature_points[0][user_id]": str(create_admin_user.id),
                },
                base_url="https://localhost",
            )
    finally:
        if fail_signature_commit is not None:
            event.remove(Session, "before_commit", fail_signature_commit)

    db_session.expire_all()
    assert db_session.scalars(select(DocToSigne)).all() == []
    assert db_session.scalars(select(Points)).all() == []
    assert db_session.scalars(select(Invitation)).all() == []
    assert pdf_path.read_bytes() == b"signature-pdf"
    assert not list(final_dir.iterdir())
