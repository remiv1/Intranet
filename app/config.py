import os
from dotenv import load_dotenv
from typing import TypedDict

# Création du chemin absolu du répertoire racine du projet
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))

#Injection des variables d'environnement
load_dotenv(env_path, override=True)

class Config:
    #Gestion base de données
    SECRET_KEY: str = os.getenv('SECRET_KEY', '')
    DB_USER: str = os.getenv('DB_USER', '')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_HOST: str = os.getenv('DB_HOST', '')
    DB_NAME: str = os.getenv('DB_NAME', '')
    #Gestion SSH
    UPLOAD_FOLDER: str = os.getenv('FILES_DOCKER_PATH', '')
    SSH_PORT: int = int(os.getenv('SSH_PORT', 22))
    SSH_HOST: str = os.getenv('SSH_HOST', 'localhost')
    SSH_USER: str = os.getenv('SSH_USER', 'user')
    SSH_PASSWORD: str = os.getenv('SSH_PASSWORD', '')
    #Gestion impression
    PRINTER_NAME: str = os.getenv('PRINTER_NAME', '')
    PRINT_PATH: str = os.getenv('PRINT_DOCKER_PATH', '')
    #Gestion mail
    EMAIL_USER: str = os.getenv('EMAIL_USER', '')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_SMTP: str = os.getenv('EMAIL_SMTP', '')
    EMAIL_PORT: int = int(os.getenv('EMAIL_PORT', 587))

class ConfigDict(TypedDict, total=False):
    SECRET_KEY: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_NAME: str
    UPLOAD_FOLDER: str
    SSH_PORT: int
    SSH_HOST: str
    SSH_USER: str
    SSH_PASSWORD: str
    PRINTER_NAME: str
    PRINT_PATH: str
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    EMAIL_SMTP: str
    EMAIL_PORT: int