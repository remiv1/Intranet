"""Tests des frontières d’exceptions des services d’impression et de signature."""

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from cryptography.exceptions import UnsupportedAlgorithm
from flask import Flask, request
from pypdf.errors import PdfReadError
from reportlab.pdfbase.pdfdoc import PDFError

from app.impression import DEFAULT_PRINTER_IP, get_cups_server, print_file
from app.models import DocToSigne
from app.signatures import SecureCertificateManager, SecureDocumentAccess
from app.signatures.signature_maker import SignatureMaker
from app.signatures.signed_document_creator import CairoError, SignedDocumentCreator


@pytest.mark.parametrize(
    "failure",
    (
        OSError("route unavailable"),
        subprocess.CalledProcessError(1, "ip route"),
        subprocess.CompletedProcess(["ip"], 0, stdout="default", stderr=""),
    ),
)
def test_get_cups_server_uses_fallback_for_expected_system_failures(
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
) -> None:
    """Les erreurs réseau/processus et la sortie de route invalide utilisent le fallback."""
    if isinstance(failure, subprocess.CompletedProcess):
        run = Mock(return_value=failure)
    else:
        run = Mock(side_effect=failure)
    monkeypatch.setattr("app.impression.subprocess.run", run)

    assert get_cups_server() == DEFAULT_PRINTER_IP


def test_get_cups_server_does_not_swallow_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une erreur de programmation inattendue ne déclenche pas le fallback CUPS."""
    monkeypatch.setattr(
        "app.impression.subprocess.run",
        Mock(side_effect=TypeError("invalid subprocess arguments")),
    )

    with pytest.raises(TypeError, match="invalid subprocess arguments"):
        get_cups_server()


def test_print_file_wraps_subprocess_errors_but_not_programming_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Les erreurs subprocess deviennent RuntimeError, pas les erreurs de programmation."""
    monkeypatch.setattr("app.impression.get_cups_server", lambda: DEFAULT_PRINTER_IP)
    monkeypatch.setattr("app.impression.get_printer_name", lambda: "test-printer")
    monkeypatch.setattr(
        "app.impression.subprocess.run",
        Mock(side_effect=subprocess.CalledProcessError(1, "lp")),
    )
    with pytest.raises(RuntimeError, match="Erreur lors de l'impression"):
        print_file("document.pdf")

    monkeypatch.setattr(
        "app.impression.subprocess.run",
        Mock(side_effect=TypeError("invalid subprocess arguments")),
    )
    with pytest.raises(TypeError, match="invalid subprocess arguments"):
        print_file("document.pdf")


def test_create_secure_certificate_wraps_supported_crypto_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Les indisponibilités cryptographiques sont converties en ValueError."""
    document = DocToSigne(hash_fichier="document-hash")
    monkeypatch.setattr(
        SecureCertificateManager,
        "generate_signing_key",
        Mock(side_effect=UnsupportedAlgorithm("key algorithm unavailable")),
    )

    with pytest.raises(ValueError, match="Erreur lors de la création"):
        SecureCertificateManager.create_secure_certificate(
            signatures=[],
            signatories=[],
            document=document,
        )


def test_create_secure_certificate_does_not_wrap_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Les erreurs inattendues de création ne sont pas masquées en ValueError."""
    document = DocToSigne(hash_fichier="document-hash")
    monkeypatch.setattr(
        SecureCertificateManager,
        "generate_signing_key",
        Mock(side_effect=AttributeError("unexpected implementation error")),
    )

    with pytest.raises(AttributeError, match="unexpected implementation error"):
        SecureCertificateManager.create_secure_certificate(
            signatures=[],
            signatories=[],
            document=document,
        )


def test_verify_certificate_wraps_invalid_public_key(
) -> None:
    """Une clé publique invalide est rapportée comme certificat invalide."""
    with pytest.raises(ValueError, match="Échec de la vérification"):
        SecureCertificateManager.verify_certificate({
            "certificate": {},
            "cryptographic_signature": "00",
            "public_key": "not a public key",
        })


def test_verify_certificate_does_not_wrap_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une erreur inattendue du chargeur de clé publique reste visible."""
    monkeypatch.setattr(
        "app.signatures.secure_certificate_manager.serialization.load_pem_public_key",
        Mock(side_effect=AttributeError("unexpected key loader error")),
    )

    with pytest.raises(AttributeError, match="unexpected key loader error"):
        SecureCertificateManager.verify_certificate({
            "certificate": {},
            "cryptographic_signature": "00",
            "public_key": "valid-shaped-input",
        })


@pytest.mark.parametrize("failure", (OSError("move failed"), TypeError("move bug")))
def test_fix_documents_only_wraps_filesystem_errors(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: Exception,
) -> None:
    """Le déplacement convertit les erreurs disque, mais laisse remonter TypeError."""
    temp_dir = tmp_path / "temporary"
    temp_dir.mkdir()
    (temp_dir / "source.pdf").write_bytes(b"pdf")
    monkeypatch.setattr(SecureDocumentAccess, "TEMP_DIR", str(temp_dir))
    monkeypatch.setenv("SIGNATURE_DOCKER_PATH", str(tmp_path / "final"))
    monkeypatch.setattr("app.signatures.signature_maker.shutil.move", Mock(side_effect=failure))

    with app.test_request_context("/"):
        maker = SignatureMaker(request)
        maker.old_name = "source.pdf"
        maker.new_name = "target.pdf"
        maker.doc_to_signe.id = 123
        expected_error = OSError if isinstance(failure, OSError) else TypeError
        with pytest.raises(expected_error):
            maker.fix_documents()


def test_apply_signatures_wraps_pdf_errors_and_propagates_unexpected_errors(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Les erreurs pypdf sont converties; une erreur inattendue ne l’est pas."""
    with app.test_request_context("/"):
        creator = SignedDocumentCreator(id_document=1)
        creator.document_path = tmp_path / "original.pdf"
        creator.view_points = [{}]
        fallback = Mock()
        monkeypatch.setattr(
            creator,
            "_prepare_signed_document",
            Mock(side_effect=PdfReadError("bad pdf")),
        )
        monkeypatch.setattr(creator, "_create_fallback_copy", fallback)
        with pytest.raises(ValueError, match="Erreur lors de l'application des signatures"):
            creator.apply_signatures_to_pdf()
        fallback.assert_called_once_with()

        monkeypatch.setattr(
            creator,
            "_prepare_signed_document",
            Mock(side_effect=AttributeError("unexpected pdf bug")),
        )
        with pytest.raises(AttributeError, match="unexpected pdf bug"):
            creator.apply_signatures_to_pdf()
        fallback.assert_called_once_with()


def test_signature_overlay_wraps_reportlab_errors_and_propagates_unexpected_errors(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Les erreurs ReportLab deviennent ValueError, sans capturer TypeError."""
    with app.test_request_context("/"):
        creator = SignedDocumentCreator(id_document=1)
        page = SimpleNamespace(mediabox=SimpleNamespace(width=612, height=792))
        monkeypatch.setattr(
            SignedDocumentCreator,
            "_add_single_signature_to_canvas",
            Mock(side_effect=PDFError("invalid canvas")),
        )
        create_overlay = getattr(creator, "_create_signature_overlay")
        with pytest.raises(ValueError, match="Impossible de créer l'overlay"):
            create_overlay(page, [{}])

        monkeypatch.setattr(
            SignedDocumentCreator,
            "_add_single_signature_to_canvas",
            Mock(side_effect=TypeError("unexpected overlay bug")),
        )
        with pytest.raises(TypeError, match="unexpected overlay bug"):
            create_overlay(page, [{}])


def test_convert_svg_wraps_xml_errors_but_propagates_unexpected_errors(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un SVG mal formé devient ValueError, tandis qu’un TypeError remonte."""
    with app.test_request_context("/"):
        creator = SignedDocumentCreator(id_document=1)
        convert_svg = getattr(creator, "_convert_svg_to_image")
        with pytest.raises(ValueError, match="Erreur lors de la conversion SVG"):
            convert_svg(svg_content="<svg><path>", width=10, height=10)

        monkeypatch.setattr(
            "app.signatures.signed_document_creator.cairosvg.svg2png",
            Mock(side_effect=TypeError("unexpected SVG bug")),
        )
        with pytest.raises(TypeError, match="unexpected SVG bug"):
            convert_svg(
                svg_content='<svg xmlns="http://www.w3.org/2000/svg"/>',
                width=10,
                height=10,
            )


def test_convert_svg_wraps_cairo_render_errors(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une erreur du moteur Cairo est convertie en erreur de conversion SVG."""
    with app.test_request_context("/"):
        creator = SignedDocumentCreator(id_document=1)
        monkeypatch.setattr(
            "app.signatures.signed_document_creator.cairosvg.svg2png",
            Mock(side_effect=CairoError("render failed", 1)),
        )

        convert_svg = getattr(creator, "_convert_svg_to_image")
        with pytest.raises(ValueError, match="Erreur lors de la conversion SVG"):
            convert_svg(
                svg_content='<svg xmlns="http://www.w3.org/2000/svg"/>',
                width=10,
                height=10,
            )


def test_add_signature_certificates_wraps_crypto_errors_and_propagates_unexpected_errors(
    app: Flask,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Les erreurs cryptographiques sont converties sans masquer les erreurs inattendues."""
    with app.test_request_context("/"):
        creator = SignedDocumentCreator(id_document=1)
        creator.signed_document_path = tmp_path / "signed.pdf"
        creator.signatures = [Mock()]
        monkeypatch.setattr(
            SecureCertificateManager,
            "create_secure_certificate",
            Mock(side_effect=UnsupportedAlgorithm("unsupported key")),
        )
        with pytest.raises(ValueError, match="Erreur lors de l'ajout des certificats"):
            creator.add_signature_certificates()

        monkeypatch.setattr(
            SecureCertificateManager,
            "create_secure_certificate",
            Mock(side_effect=AttributeError("unexpected certificate bug")),
        )
        with pytest.raises(AttributeError, match="unexpected certificate bug"):
            creator.add_signature_certificates()
