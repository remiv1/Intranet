"""
Module de gestion des documents pour l'application Intranet de la Péraudière.
Ce module fournit des fonctions pour le téléchargement, le renommage, la suppression,
le téléchargement et l'impression de fichiers sur le serveur.
Il utilise des chemins sécurisés pour éviter les problèmes de sécurité liés aux fichiers,
et gère les erreurs de manière robuste pour assurer une expérience utilisateur fluide.
"""

import os
import io
from os.path import splitext
from logging import getLogger
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask import jsonify, send_file
from .impression import print_file
from app.config.config import ConfigApp

logger = getLogger(__name__)

# Définition des variables de gestion (évaluées lors de la première utilisation)
def _get_folder() -> str:
    return ConfigApp.UPLOAD_FOLDER

def _get_print_folder() -> str:
    return ConfigApp.PRINT_PATH

# Validation des chemins (appelée lors du premier accès)
_folder_initialized = False # pylint: disable=invalid-name

# S'assurer que le dossier existe
def _ensure_folder_exists():
    global _folder_initialized  # pylint: disable=global-statement
    if not _folder_initialized:
        folder = _get_folder()
        if not os.path.exists(folder):
            os.makedirs(folder)
        _folder_initialized = True

# Téléchargement du fichier vers le serveur
def upload_file(file_to_upload: FileStorage, *, file_name: str):
    """Télécharge un fichier vers le serveur en utilisant un nom de fichier sécurisé.
    Arguments:
        file_to_upload (FileStorage): Le fichier à télécharger, généralement obtenu
                                      depuis une requête Flask.
        file_name (str): Le nom de fichier souhaité pour le fichier sur le serveur
                         (sans extension).
    Retourne:
        None
    """
    _ensure_folder_exists()  # S'assurer que le dossier existe

    # Création du chemin du fichier sur le serveur
    if file_to_upload.filename:
        extension = splitext(file_to_upload.filename)[1] or '.any'
    else:
        extension = '.any'
    file_name = secure_filename(splitext(file_name)[0]) + extension
    file_path = os.path.join(_get_folder(), file_name)

    # Enregistrement du fichier sur le serveur
    with open(file_path, 'wb') as f:
        f.write(file_to_upload.read())

# Transfert de deux fichiers (exchange files)
def exchange_files(old_file_name: str, new_file: FileStorage, new_file_name: str):
    """
    Fonction pour échanger un fichier existant sur le serveur avec un nouveau fichier.
    Supprime l'ancien fichier et enregistre le nouveau fichier avec un nom
                potentiellement différent.
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
        new_file_path = os.path.join(_get_folder(), secure_filename(new_file_name))

        # Enregistrement du nouveau fichier sur le serveur
        with open(new_file_path, 'wb') as f:
            f.write(new_file.read())

        return True

    except Exception:
        return False


def rename_file(old_file_name: str, new_file_name: str):
    """Renomme un fichier existant sur le serveur.
    Arguments:
        old_file_name (str): Le nom actuel du fichier sur le serveur (avec extension).
        new_file_name (str): Le nom souhaité pour le fichier sur le serveur (avec extension).
    Retourne:
        bool: True si le renommage a réussi, False sinon.
    """
    _ensure_folder_exists()  # S'assurer que le dossier existe

    try:
        # Création des chemins des fichiers sur le serveur
        old_file_path = os.path.join(_get_folder(), secure_filename(old_file_name))
        new_file_path = os.path.join(_get_folder(), secure_filename(new_file_name))

        # Renommage du fichier sur le serveur
        if os.path.exists(old_file_path):
            os.rename(old_file_path, new_file_path)
            return True
        else:
            return False

    except Exception:
        return False

def download_file(file_name_with_ext: str):
    """Télécharge un fichier depuis le serveur vers le client.
    Arguments:
        file_name_with_ext (str): Le nom du fichier à télécharger (avec extension).
    Retourne:
        Response: Un objet de réponse Flask contenant le fichier à télécharger,
                  ou une réponse JSON en cas d'erreur.
    """
    _ensure_folder_exists()  # S'assurer que le dossier existe

    try:
        # Création du chemin du fichier sur le serveur
        remote_file_path = os.path.join(_get_folder(), secure_filename(file_name_with_ext))

        # Transfert du fichier depuis le serveur
        with open(remote_file_path, 'rb') as f:
            file_data = f.read()

        # Création d'un objet pour envoyer le fichier au client
        file_stream = io.BytesIO(file_data)
        file_stream.seek(0)

        return send_file(
            file_stream,
            as_attachment=True,
            download_name=secure_filename(file_name_with_ext)
            )

    except FileNotFoundError:
        return jsonify({'erreur': f'Erreur de fichier introuvable : {file_name_with_ext}'}), 404
    except Exception as e:
        return jsonify({'erreur': f'Erreur inconnue lors du téléchargement : {e}'})

def delete_file(file_name: str, extension: str):
    """Supprime un fichier existant sur le serveur.
    Arguments:
        file_name (str): Le nom du fichier à supprimer (sans extension).
        extension (str): L'extension du fichier à supprimer.
    Retourne:
        Response: Un objet de réponse Flask contenant le résultat de la suppression.
    """
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
def print_document(
        file: io.BytesIO,
        file_name: str,
        extension: str,
        copies: str,
        username: str,
        sides: str,
        media: str,
        orientation: str,
        color: str
        ):
    """Imprime un document en utilisant les paramètres spécifiés.
    Arguments:
        file (io.BytesIO): Le contenu du fichier à imprimer.
        file_name (str): Le nom du fichier à imprimer (sans extension).
        extension (str): L'extension du fichier à imprimer.
        copies (str): Le nombre de copies à imprimer.
        username (str): Le nom de l'utilisateur qui imprime le document.
        sides (str): Le mode d'impression recto-verso (ex: 'one-sided', 'two-sided-long-edge').
        media (str): Le format de papier à utiliser (ex: 'A4', 'Letter').
        orientation (str): L'orientation de l'impression (ex: '3' pour portrait, '4' pour paysage).
        color (str): Le mode de couleur à utiliser (ex: 'monochrome', 'color').
    Retourne:
        Response: Un objet de réponse Flask indiquant le résultat de l'impression.
    """
    try:
        # Création du chemin du fichier sur le serveur
        file_name = secure_filename(file_name) + '.' + extension
        file_path = os.path.join(_get_print_folder(), file_name)
        logger.info("Preparing to print file: %s", file_path)

        # Transfert du fichier vers le serveur
        with open(file_path, 'wb') as f:
            f.write(file.read())
            logger.info("File %s written to print directory", file_path)

        # Impression du fichier
        print_file(file_path, username, 'Intranet' , copies, sides, media, orientation, color)
        logger.info("Print command sent for file: %s", file_path)
        os.remove(file_path)
        logger.info("File %s removed from print directory after printing", file_path)

        return jsonify({'message': 'Document imprimé avec succès'})

    except Exception as e:
        logger.exception("Erreur lors de l'impression")
        return jsonify({'erreur': f'Erreur lors de l\'impression : {e}'})
