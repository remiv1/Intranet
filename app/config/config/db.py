"""Module de configuration de la base de données.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations
from os import getenv
from dataclasses import dataclass
from datetime import timedelta
from sqlalchemy.engine.url import URL

@dataclass
class ConfigDB:
    """
    Classe de configuration de la base de données, utilisant les variables d'environnement
    chargées depuis le fichier .env.
    :param DB_USER: Nom d'utilisateur de la base de données.
    :type DB_USER: str
    :param DB_PASSWORD: Mot de passe de la base de données.
    :type DB_PASSWORD: str
    :param DB_HOST: Adresse du serveur de base de données.
    :type DB_HOST: str
    :param DB_NAME: Nom de la base de données.
    :type DB_NAME: str
    :param DB_URL: URL de connexion à la base de données.
    :type DB_URL: URL
    :param PERMANENT_SESSION_LIFETIME: Durée de vie de la session permanente.
    :type PERMANENT_SESSION_LIFETIME: timedelta

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    # Gestion base de données
    DB_USER: str = getenv('DB_USER', '') # pylint: disable=C0103
    DB_PASSWORD: str = getenv('DB_PASSWORD', '') # pylint: disable=C0103
    DB_HOST: str = getenv('DB_HOST', '') # pylint: disable=C0103
    DB_NAME: str = getenv('DB_NAME', '') # pylint: disable=C0103
    DB_URL: URL = URL.create(  # pylint: disable=C0103
        drivername="mysql+mysqlconnector",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=3306,
        database=DB_NAME,
        query={"charset": "utf8mb4"}
    )
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(minutes=30) # pylint: disable=C0103
