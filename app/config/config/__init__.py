"""Module d'initialisation du package de configuration.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from .db import ConfigDB
from .app import ConfigApp
from .mail import ConfigMail
from .ttlama import ConfigTTLLama

# Création du chemin absolu du répertoire racine du projet
env_path = Path(__file__).parent.parent / '.env'

# Injection des variables d'environnement
load_dotenv(env_path, override=True)

__all__ = [
    "ConfigDB",
    "ConfigApp",
    "ConfigMail",
    "ConfigTTLLama"
]
