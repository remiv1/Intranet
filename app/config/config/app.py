"""Module de configuration de l'application.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from os import getenv
from dataclasses import dataclass, field
from datetime import timedelta

@dataclass
class ConfigApp:    # pylint: disable=R0902
    """ConfigApp est une class pour la configuration de l'application Flask
    
    :param SECRET_KEY: Clé secrète de l'application Flask.
    :type SECRET_KEY: str
    :param UPLOAD_FOLDER: Dossier de téléchargement des fichiers.
    :type UPLOAD_FOLDER: str
    :param UPLOAD_EXTENSIONS: Extensions de fichiers autorisées pour le téléchargement.
    :type UPLOAD_EXTENSIONS: list[str]
    :param SSH_PORT: Port SSH pour la connexion.
    :type SSH_PORT: int
    :param SSH_HOST: Hôte SSH pour la connexion.
    :type SSH_HOST: str
    :param SSH_USER: Utilisateur SSH pour la connexion.
    :type SSH_USER: str
    :param SSH_PASSWORD: Mot de passe SSH pour la connexion.
    :type SSH_PASSWORD: str
    :param PRINTER_NAME: Nom de l'imprimante.
    :type PRINTER_NAME: str
    :param PRINT_PATH: Chemin de téléchargement pour l'impression.
    :type PRINT_PATH: str

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """

    # Gestion SSH
    SECRET_KEY: str = getenv('SECRET_KEY', '') # pylint: disable=C0103
    UPLOAD_FOLDER: str = getenv('FILES_DOCKER_PATH', '') # pylint: disable=C0103
    UPLOAD_EXTENSIONS: list[str] = field(   # pylint: disable=C0103
        default_factory=lambda: ['.jpg', '.png', '.gif', '.jpeg', '.tif', '.tiff', '.pdf']
        )
    SSH_PORT: int = int(getenv('SSH_PORT', '22')) # pylint: disable=C0103
    SSH_HOST: str = getenv('SSH_HOST', 'localhost') # pylint: disable=C0103
    SSH_USER: str = getenv('SSH_USER', 'user') # pylint: disable=C0103
    SSH_PASSWORD: str = getenv('SSH_PASSWORD', '') # pylint: disable=C0103
    # Gestion impression
    PRINTER_NAME: str = getenv('PRINTER_NAME', '') # pylint: disable=C0103
    PRINT_PATH: str = getenv('PRINT_DOCKER_PATH', '') # pylint: disable=C0103
    # Gestion CSRF
    CSRF_ENABLED: bool = True # pylint: disable=C0103
    # Gestion des cookies de session
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(minutes=20) # pylint: disable=C0103
    SESSION_COOKIE_NAME: str = 'session' # pylint: disable=C0103
    SESSION_COOKIE_SECURE: bool = True # pylint: disable=C0103
    SESSION_COOKIE_HTTPONLY: bool = True # pylint: disable=C0103
    SESSION_COOKIE_SAMESITE: str = 'Lax' # pylint: disable=C0103
