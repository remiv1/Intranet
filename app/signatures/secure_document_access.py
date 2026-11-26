"""Module pour gérer l'accès sécurisé aux documents via des fichiers temporaires.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from pathlib import Path
from typing import Any
from os import getenv
import json

from flask import session, request

from ._common import DEFAULT_TEMP_DIR

class SecureDocumentAccess:
    """Classe pour gérer l'accès sécurisé aux documents via fichiers temporaires.

    :param TEMP_DIR: Le chemin du dossier temporaire pour les fichiers d'accès.
    :type TEMP_DIR: str

    .. methods::
        -`get_user_identifier()`: Génère un identifiant unique pour l'utilisateur basé sur session,
        IP et User-Agent.
        -`generate_document_hash(filename: str, user_identifier: str | None = None) -> str`: Génère
        un hash sécurisé pour le document avec HMAC.
        -`create_temp_access_file(filename: str, document_hash: str) -> None`: Crée un fichier JSON
        temporaire avec les informations d'accès.
        -`verify_temp_access(filename: str) -> bool`: Vérifie l'accès au document via les fichiers
        temporaires.
        -`cleanup_expired_temp_files() -> None`: Nettoie les fichiers temporaires expirés.
    """
    # Constante pour le dossier temporaire
    TEMP_DIR = getenv('TEMP_DOCKER_PATH', DEFAULT_TEMP_DIR) + '/signature'

    @staticmethod
    def get_user_identifier() -> str:
        """Génère un identifiant unique pour l'utilisateur basé sur session, IP et User-Agent.

        :return: L'identifiant unique de l'utilisateur.
        :rtype: str

        .. example::
            .. code-block:: python
            user_id = SecureDocumentAccess.get_user_identifier()
        """
        # Récupération des informations utilisateur dans la session et la requête
        user_id: str = session.get('identifiant', 'anonymous')
        ip_address: str = request.remote_addr or 'unknown'
        user_agent: str = request.headers.get('User-Agent', 'unknown')[:50]

        # Utiliser MD5 pour raccourcir le User-Agent
        ua_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]

        return f"{user_id}-{ip_address}-{ua_hash}"

    @staticmethod
    def generate_document_hash(filename: str, user_identifier: str | None = None) -> str:
        """Génère un hash sécurisé pour le document avec HMAC.

        :param filename: Le nom du fichier.
        :type filename: str
        :param user_identifier: L'identifiant unique de l'utilisateur.
        :type user_identifier: str | None

        :return: Le hash sécurisé du document.
        :rtype: str

        .. example::
            .. code-block:: python
            doc_hash = SecureDocumentAccess.generate_document_hash('document.pdf')
        """
        # Génération de l'identifiant utilisateur si non fourni
        if not user_identifier:
            user_identifier = SecureDocumentAccess.get_user_identifier()

        # Génération du hash HMAC avec SHA-256
        secret_key = getenv('SECRET_KEY', 'default-secret-key')
        timestamp = datetime.now().isoformat()[:19]  # YYYY-MM-DDTHH:MM:SS
        message = f"{filename}-{user_identifier}-{timestamp}"
        document_hash = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return document_hash

    @staticmethod
    def create_temp_access_file(filename: str, document_hash: str) -> None:
        """Crée un fichier JSON temporaire avec les informations d'accès.

        :param filename: Le nom du fichier.
        :type filename: str
        :param document_hash: Le hash sécurisé du document.
        :type document_hash: str

        :return: None
        :rtype: None

        .. example::
            .. code-block:: python
            SecureDocumentAccess.create_temp_access_file('document.pdf', 'abc123hash')
        """
        # Création du dossier temporaire s'il n'existe pas
        temp_dir = Path(SecureDocumentAccess.TEMP_DIR)
        temp_dir.mkdir(exist_ok=True)

        # Données à stocker dans le fichier JSON
        access_data: dict[str, Any] = {
            "filename": filename,
            "hash": document_hash,
            "user_identifier": SecureDocumentAccess.get_user_identifier(),
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now().timestamp() + 86400)  # 24h en secondes
        }

        # Nom du fichier JSON basé sur le hash
        json_file = temp_dir / f"{document_hash}.json"

        # Écriture des données dans le fichier JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(access_data, f, indent=2)

        return None

    @staticmethod
    def verify_temp_access(filename: str) -> bool:
        """Vérifie l'accès au document via les fichiers temporaires.

        :param filename: Le nom du fichier à vérifier.
        :type filename: str

        :return: True si l'accès est valide, False sinon.
        :rtype: bool

        .. example::
            .. code-block:: python
            is_valid = SecureDocumentAccess.verify_temp_access('document.pdf')
        """
        # Génération de l'identifiant utilisateur si non fourni
        user_identifier = SecureDocumentAccess.get_user_identifier()
        temp_dir = Path(SecureDocumentAccess.TEMP_DIR)

        # Vérifier si le dossier temporaire existe
        if not temp_dir.exists():
            return False

        # Chercher tous les fichiers JSON dans temp/
        json_files = list(temp_dir.glob("*.json"))

        # Vérifier chaque fichier JSON existant dans temp/
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    access_data = json.load(f)

                # Vérifier que le fichier correspond
                if access_data.get("filename") != filename:
                    continue

                # Vérifier l'utilisateur
                if access_data.get("user_identifier") != user_identifier:
                    continue

                # Vérifier l'expiration
                expires_at = access_data.get("expires_at", 0)
                current_time = datetime.now().timestamp()
                if current_time > expires_at:
                    # Supprimer le fichier expiré
                    json_file.unlink(missing_ok=True)
                    continue

                # Accès valide trouvé
                return True

            except (json.JSONDecodeError, IOError):
                # Fichier corrompu, on l'ignore
                continue

        return False

    @staticmethod
    def cleanup_expired_temp_files() -> None:
        """Nettoie les fichiers temporaires expirés.

        :return: None
        :rtype: None

        .. example::
            .. code-block:: python
            SecureDocumentAccess.cleanup_expired_temp_files()
        """
        # Récupération du dossier temporaire
        temp_dir = Path(SecureDocumentAccess.TEMP_DIR)
        if not temp_dir.exists():
            return

        # Récupération de l'heure actuelle
        current_time = datetime.now().timestamp()

        # Parcours de tous les fichiers JSON dans temp/
        for json_file in temp_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    access_data = json.load(f)

                expires_at = access_data.get("expires_at", 0)
                if current_time > expires_at:
                    json_file.unlink(missing_ok=True)

            except (json.JSONDecodeError, IOError):
                # Fichier corrompu, on le supprime
                json_file.unlink(missing_ok=True)
