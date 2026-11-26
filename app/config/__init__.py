"""Module de configuration pour l'application.

Ce module contient les classes de configuration pour la base de données,
l'application Flask et la gestion des mails.

.. classes::
    - `ConfigDB`: Classe de configuration de la base de données.
    - `ConfigApp`: Classe de configuration de l'application Flask.
    - `ConfigMail`: Classe de configuration des mails.
"""

from .config import ConfigDB, ConfigApp, ConfigMail
from .database import engine, SESSION
from .logger import api_logger

__all__ = [
    "ConfigDB",
    "ConfigApp",
    "ConfigMail",
    "engine",
    "SESSION",
    "api_logger",
]
