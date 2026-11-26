"""
Module de gestion des documents pour l'application Intranet de la Péraudière.
Ce module fournit des fonctions pour le téléchargement, le renommage, la suppression,
le téléchargement et l'impression de fichiers sur le serveur.
Il utilise des chemins sécurisés pour éviter les problèmes de sécurité liés aux fichiers,
et gère les erreurs de manière robuste pour assurer une expérience utilisateur fluide.
"""

import os
import io
import shutil
import tempfile
from contextlib import contextmanager
from os.path import splitext
from logging import getLogger
from collections.abc import Generator
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask import jsonify, send_file
from app.config.config import ConfigApp
from .impression import print_file

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


@contextmanager
def preserve_files_on_error(
    *file_names: str,
    directory: str | Path | None = None,
) -> Generator[None, None, None]:
    """Restaure les fichiers concernés si une opération échoue.

    Args:
        file_names: Noms sécurisés des fichiers à protéger dans le dossier de dépôt.

    Yields:
        None: Le contexte de modification des fichiers.
    """
    folder = Path(directory) if directory is not None else Path(_get_folder())
    folder.mkdir(parents=True, exist_ok=True)
    snapshots: dict[Path, Path | None] = {}

    try:
        for file_name in dict.fromkeys(name for name in file_names if name):
            path = folder / secure_filename(file_name)
            if path.exists():
                descriptor, backup_name = tempfile.mkstemp(
                    prefix=".intranet-backup-", dir=folder
                )
                os.close(descriptor)
                backup = Path(backup_name)
                snapshots[path] = backup
                shutil.copy2(path, backup)
            else:
                snapshots[path] = None

        try:
            yield
        except BaseException:
            for path, backup in snapshots.items():
                path.unlink(missing_ok=True)
                if backup is not None:
                    os.replace(backup, path)
            raise
    finally:
        for backup in snapshots.values():
            if backup is not None:
                backup.unlink(missing_ok=True)

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

    # Ecrire d'abord dans le même dossier pour installer le fichier atomiquement.
    descriptor, temporary_name = tempfile.mkstemp(dir=_get_folder(), prefix=".intranet-upload-")
    try:
        with os.fdopen(descriptor, 'wb') as temporary_file:
            shutil.copyfileobj(file_to_upload.stream, temporary_file)
        os.replace(temporary_name, file_path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise

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

    folder = Path(_get_folder())
    old_path = folder / secure_filename(old_file_name)
    new_path = folder / secure_filename(new_file_name)
    descriptor, temporary_name = tempfile.mkstemp(dir=folder, prefix=".intranet-upload-")
    temporary_path = Path(temporary_name)
    backup_path: Path | None = None

    try:
        with os.fdopen(descriptor, 'wb') as temporary_file:
            shutil.copyfileobj(new_file.stream, temporary_file)

        if old_path != new_path and old_path.exists():
            backup_descriptor, backup_name = tempfile.mkstemp(
                dir=folder, prefix=".intranet-backup-"
            )
            os.close(backup_descriptor)
            backup_path = Path(backup_name)
            os.replace(old_path, backup_path)

        try:
            os.replace(temporary_path, new_path)
        except BaseException:
            if backup_path is not None:
                os.replace(backup_path, old_path)
                backup_path = None
            raise

        if backup_path is not None:
            backup_path.unlink(missing_ok=True)
            backup_path = None
        return True
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        if backup_path is not None:
            os.replace(backup_path, old_path)
        raise


def rename_file(old_file_name: str, new_file_name: str):
    """Renomme un fichier existant sur le serveur.
    Arguments:
        old_file_name (str): Le nom actuel du fichier sur le serveur (avec extension).
        new_file_name (str): Le nom souhaité pour le fichier sur le serveur (avec extension).
    Retourne:
        bool: True si le renommage a réussi, False sinon.
    """
    _ensure_folder_exists()  # S'assurer que le dossier existe

    old_file_path = Path(_get_folder()) / secure_filename(old_file_name)
    new_file_path = Path(_get_folder()) / secure_filename(new_file_name)
    if not old_file_path.exists():
        raise FileNotFoundError(f"Fichier source introuvable : {old_file_name}")
    os.replace(old_file_path, new_file_path)
    return True

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
    except (OSError, RuntimeError) as e:
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

    except OSError as e:
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
    file_path: str | None = None
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

        return jsonify({'message': 'Document imprimé avec succès'})

    except (OSError, RuntimeError) as e:
        logger.exception("Erreur lors de l'impression")
        return jsonify({'erreur': f'Erreur lors de l\'impression : {e}'})
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("File %s removed from print directory", file_path)
            except OSError:
                logger.exception("Impossible de supprimer le fichier de spool %s", file_path)
