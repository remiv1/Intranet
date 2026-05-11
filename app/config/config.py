"""Module de configuration de l'application."""
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
    Attributs:
        DB_USER (str): Nom d'utilisateur de la base de données.
        DB_PASSWORD (str): Mot de passe de la base de données.
        DB_HOST (str): Adresse du serveur de base de données.
        DB_NAME (str): Nom de la base de données.
    """
    # Gestion base de données
    DB_USER: str = os.getenv('DB_USER', '')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_HOST: str = os.getenv('DB_HOST', '')
    DB_NAME: str = os.getenv('DB_NAME', '')
    DB_URL: URL = URL.create(
        drivername="mysql+mysqlconnector",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=3306,
        database=DB_NAME,
        query={"charset": "utf8mb4"}
    )
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(minutes=30)


@dataclass
class ConfigApp:
    # Gestion SSH
    SECRET_KEY: str = os.getenv('SECRET_KEY', '')
    UPLOAD_FOLDER: str = os.getenv('FILES_DOCKER_PATH', '')
    UPLOAD_EXTENSIONS: list[str] = field(
        default_factory=lambda: ['.jpg', '.png', '.gif', '.jpeg', '.tif', '.tiff', '.pdf']
        )
    SSH_PORT: int = int(os.getenv('SSH_PORT', '22'))
    SSH_HOST: str = os.getenv('SSH_HOST', 'localhost')
    SSH_USER: str = os.getenv('SSH_USER', 'user')
    SSH_PASSWORD: str = os.getenv('SSH_PASSWORD', '')
    # Gestion impression
    PRINTER_NAME: str = os.getenv('PRINTER_NAME', '')
    PRINT_PATH: str = os.getenv('PRINT_DOCKER_PATH', '')


@dataclass
class ConfigMail:
    # Gestion mail
    EMAIL_USER: str = os.getenv('EMAIL_USER', '')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_SMTP: str = os.getenv('EMAIL_SMTP', '')
    EMAIL_PORT: int = int(os.getenv('EMAIL_PORT', '587'))
    API_MAIL_TOKEN: str = os.getenv('API_MAIL_TOKEN', '')
