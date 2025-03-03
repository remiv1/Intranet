import os
from dotenv import load_dotenv

# Création du chemin absolu du répertoire racine du projet
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))

#Injection des variables d'environnement
load_dotenv(env_path, override=True)

class Config:
    #Gestion base de données
    SECRET_KEY = os.getenv('SECRET_KEY')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    #Gestion SSH
    UPLOAD_FOLDER = os.getenv('FILES_PATH')
    SSH_PORT = os.getenv('SSH_PORT')
    SSH_HOST = os.getenv('SSH_HOST')
    SSH_USER = os.getenv('SSH_USER')
    SSH_PASSWORD = os.getenv('SSH_PASSWORD')
    #Gestion impression
    PRINTER_NAME = os.getenv('PRINTER_NAME')
    PRINT_PATH = os.getenv('PRINT_PATH')