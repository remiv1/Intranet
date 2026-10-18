"""Module de configuration de l'application.

.. classes::
    - `ConfigDB`: Classe de configuration de la base de données utilisant les variables
    d'environnement chargées depuis le fichier .env.
    - `ConfigApp`: Classe de configuration de l'application utilisant les variables
    d'environnement chargées depuis le fichier .env.
    - `ConfigMail`: Classe de configuration des mails utilisant les variables
    d'environnement chargées depuis le fichier .env.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
import os
from dataclasses import dataclass, field
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy.engine.url import URL

# Création du chemin absolu du répertoire racine du projet
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))

# Injection des variables d'environnement
load_dotenv(env_path, override=True)


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
    DB_USER: str = os.getenv('DB_USER', '') # pylint: disable=C0103
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '') # pylint: disable=C0103
    DB_HOST: str = os.getenv('DB_HOST', '') # pylint: disable=C0103
    DB_NAME: str = os.getenv('DB_NAME', '') # pylint: disable=C0103
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


@dataclass
class ConfigApp:
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
    SECRET_KEY: str = os.getenv('SECRET_KEY', '') # pylint: disable=C0103
    UPLOAD_FOLDER: str = os.getenv('FILES_DOCKER_PATH', '') # pylint: disable=C0103
    UPLOAD_EXTENSIONS: list[str] = field(   # pylint: disable=C0103
        default_factory=lambda: ['.jpg', '.png', '.gif', '.jpeg', '.tif', '.tiff', '.pdf']
        )
    SSH_PORT: int = int(os.getenv('SSH_PORT', '22')) # pylint: disable=C0103
    SSH_HOST: str = os.getenv('SSH_HOST', 'localhost') # pylint: disable=C0103
    SSH_USER: str = os.getenv('SSH_USER', 'user') # pylint: disable=C0103
    SSH_PASSWORD: str = os.getenv('SSH_PASSWORD', '') # pylint: disable=C0103
    # Gestion impression
    PRINTER_NAME: str = os.getenv('PRINTER_NAME', '') # pylint: disable=C0103
    PRINT_PATH: str = os.getenv('PRINT_DOCKER_PATH', '') # pylint: disable=C0103


@dataclass
class ConfigMail:
    """ConfigMail est une class pour la configuration des mails
    
    :param EMAIL_USER: Utilisateur de l'email.
    :type EMAIL_USER: str
    :param EMAIL_PASSWORD: Mot de passe de l'email.
    :type EMAIL_PASSWORD: str
    :param EMAIL_SMTP: Serveur SMTP de l'email.
    :type EMAIL_SMTP: str
    :param EMAIL_PORT: Port du serveur SMTP.
    :type EMAIL_PORT: int
    :param API_MAIL_TOKEN: Token API pour les mails.
    :type API_MAIL_TOKEN: str

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    # Gestion mail
    EMAIL_USER: str = os.getenv('EMAIL_USER', '') # pylint: disable=C0103
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '') # pylint: disable=C0103
    EMAIL_SMTP: str = os.getenv('EMAIL_SMTP', '') # pylint: disable=C0103
    EMAIL_PORT: int = int(os.getenv('EMAIL_PORT', '587')) # pylint: disable=C0103
    API_MAIL_TOKEN: str = os.getenv('API_MAIL_TOKEN', '') # pylint: disable=C0103
