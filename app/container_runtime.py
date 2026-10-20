"""Lancement non privilegie de Gunicorn et de Supercronic dans le meme conteneur."""

import logging
import os
import signal
import subprocess
import time
from types import FrameType


def _signal_processes(processes: list[subprocess.Popen[bytes]], signum: int) -> None:
    for process in processes:
        try:
            os.killpg(process.pid, signum)
        except ProcessLookupError:
            pass


def _stop_processes(processes: list[subprocess.Popen[bytes]]) -> None:
    _signal_processes(processes, signal.SIGTERM)
    deadline = time.monotonic() + 25
    for process in processes:
        try:
            process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            _signal_processes([process], signal.SIGKILL)
            process.wait()


def _wait_for_service(processes: list[subprocess.Popen[bytes]]) -> int:
    while processes:
        pid, status = os.waitpid(-1, 0)
        for process in processes:
            if process.pid == pid:
                process.returncode = os.waitstatus_to_exitcode(status)
                return process.returncode if process.returncode > 0 else 1
    return 1


def supervise(commands: list[list[str]]) -> int:
    """Arrete tous les services lorsqu'un processus meurt ou qu'un signal arrive.

    Args:
        commands: Commandes des processus a lancer sans shell.

    Returns:
        int: Code de sortie du conteneur.
    """
    processes: list[subprocess.Popen[bytes]] = []
    stopping = False

    def forward_signal(signum: int, frame: FrameType | None) -> None:   # pylint: disable=W0613
        nonlocal stopping
        stopping = True
        _signal_processes(processes, signum)

    previous_handlers = {
        signum: signal.signal(signum, forward_signal)
        for signum in (signal.SIGTERM, signal.SIGINT)
    }
    try:
        for command in commands:
            if stopping:
                return 0
            process = subprocess.Popen(command, start_new_session=True)
            processes.append(process)
            if stopping:
                _signal_processes([process], signal.SIGTERM)
        exit_code = _wait_for_service(processes)
        return 0 if stopping else exit_code
    finally:
        _stop_processes(processes)
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


def main() -> int:
    """Valide la configuration avant de lancer le serveur et le crontab.

    Returns:
        int: Code de sortie de la supervision ou du controle de configuration.
    """
    from .config.database import initialize_database    # pylint: disable=C0415
    from .rapport_echeances import validate_report_configuration    # pylint: disable=C0415

    try:
        validate_report_configuration()
        initialize_database()
    except (RuntimeError, ImportError):
        logging.error("Demarrage refuse : verifier la configuration du rapport et de la base.")
        return 1

    return supervise([
        ["supercronic", "/app/app/rapport.crontab"],
        [
            "gunicorn", "--bind", "0.0.0.0:5000",
            "--workers", os.environ.get("GUNICORN_WORKERS", "2"),
            "--access-logfile", "-", "--error-logfile", "-",
            "app.application:peraudiere",
        ],
    ])


if __name__ == "__main__":
    raise SystemExit(main())
