"""Tests de la planification mensuelle et du lancement des processus du conteneur."""

import json
import os
import select
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_monthly_schedule_uses_container_timezone() -> None:
    """Ne remplace pas le fuseau choisi pour le conteneur."""
    crontab = (ROOT / "app/rapport.crontab").read_text(encoding="utf-8")
    jobs = [line for line in crontab.splitlines() if line and not line.startswith("#")]

    assert len(jobs) == 1
    assert jobs[0].split(maxsplit=5)[:5] == ["0", "3", "1", "*", "*"]
    assert "TZ=" not in crontab
    assert "API_MAIL_TOKEN" not in crontab


def test_supercronic_accepts_crontab() -> None:
    """Fait verifier le crontab par le vrai binaire, sans executer la tache."""
    result = subprocess.run(
        ["supercronic", "-test", str(ROOT / "app/rapport.crontab")],
        capture_output=True, text=True, check=False, timeout=10,
    )

    assert result.returncode == 0, result.stderr


def test_scheduled_request_uses_json_and_private_header(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifie curl sans reseau et sans secret dans ses arguments."""
    capture = tmp_path / "request.json"
    curl = tmp_path / "curl"
    curl.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['CURL_CAPTURE']).write_text(json.dumps({"
        "'args': sys.argv[1:], 'headers': sys.stdin.read()}))\n",
        encoding="utf-8",
    )
    curl.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("API_MAIL_TOKEN", "scheduler-test-token")
    monkeypatch.setenv("CURL_CAPTURE", str(capture))

    result = subprocess.run(
        ["sh", str(ROOT / "app/rapport_cron.sh")],
        capture_output=True, text=True, check=False, timeout=10,
    )

    assert result.returncode == 0, result.stderr
    request = json.loads(capture.read_text(encoding="utf-8"))
    arguments = request["args"]
    assert "http://localhost:5000/rapport-contrats" in arguments
    assert "--fail" in arguments
    assert "--max-time" in arguments
    assert "@-" in arguments
    assert "Content-Type: application/json" in arguments
    assert json.loads(arguments[arguments.index("--data") + 1]) == {
        "email": "direction@peraudiere.com"
    }
    assert request["headers"] == "X-API-TOKEN: scheduler-test-token\n"
    assert "scheduler-test-token" not in " ".join(arguments)


def test_supervisor_stops_sibling_after_process_failure() -> None:
    """Verifie qu'un service mort ne laisse pas l'autre tourner seul."""
    program = """
import sys
from app.container_runtime import supervise

raise SystemExit(supervise([
    [sys.executable, '-c', 'import signal; signal.pause()'],
    [sys.executable, '-c', 'raise SystemExit(7)'],
]))
"""
    result = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True, text=True, check=False, timeout=10,
    )

    assert result.returncode == 7, result.stderr


def test_supervisor_forwards_shutdown_signal() -> None:
    """Verifie qu'un SIGTERM arrete les deux processus sans erreur."""
    program = """
import sys
from app.container_runtime import supervise

child = [sys.executable, '-c', 'import signal; print("ready", flush=True); signal.pause()']
raise SystemExit(supervise([child, child]))
"""
    process = subprocess.Popen(
        [sys.executable, "-c", program], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        assert process.stdout is not None
        readable, _, _ = select.select([process.stdout], [], [], 5)
        assert readable, "Les processus supervises ne sont pas demarres."
        assert process.stdout.readline() == b"ready\n"
        process.terminate()
        _, stderr = process.communicate(timeout=10)

        assert process.returncode == 0, stderr.decode()
    finally:
        if process.poll() is None:
            process.terminate()
            process.communicate(timeout=10)
