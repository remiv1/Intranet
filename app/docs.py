from flask import jsonify, send_file
from werkzeug.utils import secure_filename
import os, io, datetime
from os.path import splitext
from config import ConfigDict
from typing import cast
from impression import print_file
from logging import getLogger

logger = getLogger(__name__)

def get_config() -> ConfigDict:
    """Import tardif pour éviter l'import circulaire"""
    from application import peraudiere
    return cast(ConfigDict, peraudiere.config)

# Définition des variables de gestion (évaluées lors de la première utilisation)
def _get_folder() -> str:
    return get_config().get("UPLOAD_FOLDER", '/uploads')

def _get_print_folder() -> str:
    return get_config().get("PRINT_PATH", '/prints')

# Validation des chemins (appelée lors du premier accès)
_folder_initialized = False

# S'assurer que le dossier existe
def _ensure_folder_exists():
    global _folder_initialized
    if not _folder_initialized:
        folder = _get_folder()
        if not os.path.exists(folder):
            os.makedirs(folder)
        _folder_initialized = True

# Création d'un nom de docment
def create_name(doc_date: str, id_contrat: str, id_document: str, sous_type_document: str):
    date_date = datetime.datetime.strptime(doc_date, '%Y-%m-%d')
    str_date = date_date.strftime('%d%m%Y')
    id_contrat = str(id_contrat).zfill(3)
    id_document = str(id_document).zfill(4)
    sous_type_document = sous_type_document[:5]
    retour = f'{str_date}_{id_contrat}_{id_document}_{sous_type_document}'
    return retour

# Téléchargement du fichier vers le serveur
def upload_file(file: io.BytesIO, file_name: str, extension: str):
    _ensure_folder_exists()  # S'assurer que le dossier existe
    
    try:
        # Création du chemin du fichier sur le serveur
        file_name = secure_filename(file_name) + extension
        file_path = os.path.join(_get_folder(), file_name)
        
        # Enregistrement du fichier sur le serveur
        with open(file_path, 'wb') as f:
            f.write(file.read())

        return jsonify({'message': 'File uploaded successfully'})
    
    except Exception as e:
        return jsonify({'erreur': f'Erreur lors de la sauvegarde locale : {e}'})
    
# Transfert de deux fichiers (exchange files)
def exchange_files(old_file_name: str, new_file: io.BytesIO, new_file_name: str, extension: str):
    """
    Fonction pour échanger un fichier existant sur le serveur avec un nouveau fichier.
    Supprime l'ancien fichier et enregistre le nouveau fichier avec un nom potentiellement différent.
    1. Supprime l'ancien fichier.
    2. Enregistre le nouveau fichier avec le nouveau nom.
    3. Gère les erreurs et retourne un booléen.
    """
    _ensure_folder_exists()  # S'assurer que le dossier existe
    
    try:
        # Suppression de l'ancien fichier
        old_file_path = os.path.join(_get_folder(), secure_filename(old_file_name))
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

        # Création du chemin du nouveau fichier sur le serveur
        new_file_name = secure_filename(new_file_name) + extension
        new_file_path = os.path.join(_get_folder(), new_file_name)
        
        # Enregistrement du nouveau fichier sur le serveur
        with open(new_file_path, 'wb') as f:
            f.write(new_file.read())

        return True
    
    except Exception:
        return False
    
# Fonction pour changer seulement le nom d'un fichier (rename file)
def rename_file(old_file_name: str, new_file_name: str, extension: str):
    _ensure_folder_exists()  # S'assurer que le dossier existe
    
    try:
        # Création des chemins des fichiers sur le serveur
        old_file_path = os.path.join(_get_folder(), secure_filename(splitext(old_file_name)[0]) + extension)
        new_file_path = os.path.join(_get_folder(), secure_filename(new_file_name) + extension)
        
        # Renommage du fichier sur le serveur
        if os.path.exists(old_file_path):
            os.rename(old_file_path, new_file_path)
            return True
        else:
            return False
    
    except Exception:
        return False
    
# Téléchargement du fichier depuis le serveur
def download_file(file_name: str, extension: str):
    _ensure_folder_exists()  # S'assurer que le dossier existe
    
    try:
        # Création du chemin du fichier sur le serveur
        remote_file_path = os.path.join(_get_folder(), secure_filename(file_name) + '.' + extension)

        # Transfert du fichier depuis le serveur
        with open(remote_file_path, 'rb') as f:
            file_data = f.read()

        # Création d'un objet pour envoyer le fichier au client
        file_stream = io.BytesIO(file_data)
        file_stream.seek(0)

        return send_file(file_stream, as_attachment=True, download_name=secure_filename(file_name) + '.' + extension)
    
    except FileNotFoundError:
        return jsonify({'erreur': f'Erreur de fichier introuvable : {file_name}.{extension}'}), 404
    except Exception as e:
        return jsonify({'erreur': f'Erreur inconnue lors du téléchargement : {e}'})
    
# Suppression du fichier depuis le serveur
def delete_file(file_name: str, extension: str):
    _ensure_folder_exists()  # S'assurer que le dossier existe
    
    try:
        # Création du chemin du fichier sur le serveur
        file_name = secure_filename(file_name) + '.' + extension
        file_path = os.path.join(_get_folder(), file_name)

        # Suppression du fichier sur le serveur
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'Fichier supprimé avec succès'})
        else:
            return jsonify({'erreur': 'Erreur lors de la suppression : dossier inexistant'})

    except Exception as e:
        return jsonify({'erreur': f'Erreur inconnue : {e}'})

# Impression du fichier vers le serveur d'impression
def print_document(file: io.BytesIO, file_name: str, extension: str, copies: str, username: str, sides: str, media: str, orientation: str, color: str):
    
    try:
        # Création du chemin du fichier sur le serveur
        file_name = secure_filename(file_name) + '.' + extension
        file_path = os.path.join(_get_print_folder(), file_name)
        logger.info(f"Preparing to print file: {file_path}")
        
        # Transfert du fichier vers le serveur
        with open(file_path, 'wb') as f:
            f.write(file.read())
            logger.info(f"File {file_path} written to print directory")
        
        # Impression du fichier
        print_file(file_path, username, 'Intranet' , copies, sides, media, orientation, color)
        logger.info(f"Print command sent for file: {file_path}")
        os.remove(file_path)
        logger.info(f"File {file_path} removed from print directory after printing")
        
        return jsonify({'message': 'Document imprimé avec succès'})
    
    except Exception as e:
        return jsonify({'erreur': f'Erreur lors de l\'impression : {e}'})
    