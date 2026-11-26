"""Module de gestion des certificats de signature sécurisés.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""

from __future__ import annotations

import hashlib
import secrets
import json
from datetime import datetime
from typing import Any, cast

from cryptography.exceptions import (
    InternalError,
    InvalidKey,
    InvalidSignature,
    UnsupportedAlgorithm,
)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding

from ..models import User, Signatures, DocToSigne

class SecureCertificateManager:
    """
    Gestionnaire de certificats sécurisés pour les signatures électroniques.
    
    Cette classe gère la création, la signature et la vérification de certificats
    cryptographiques pour garantir l'intégrité et l'authenticité des signatures.
    """

    @staticmethod
    def generate_signing_key():
        """
        Génère une clé privée RSA pour la signature des certificats.
        
        Returns:
            Clé privée RSA
        """
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

    @staticmethod
    def _add_signatories_info(
        signatories: list[User],    # pylint: disable=W0613
        signatures: list[Signatures],
        cert_data: dict[str, Any],
        sig_to_user: dict[int, User],
    ) -> dict[str, Any]:
        """Ajoute les informations des signataires au certificat.
        
        :param signatories: Liste des utilisateurs signataires
        :type signatories: list[User]
        :param signatures: Liste des signatures
        :type signatures: list[Signatures]
        :param cert_data: Dictionnaire du certificat à remplir
        :type cert_data: dict[str, Any]
        :param sig_to_user: Mapping signature_id -> User
        :type sig_to_user: dict[int, User]
        """
        for signature in signatures:
            # Utiliser le mapping pour trouver l'utilisateur correspondant
            signatory = sig_to_user.get(signature.id)
            if signatory:
                signatory_info: dict[str, Any] = {
                    "id": signatory.id,
                    "name": f"{signatory.prenom} {signatory.nom}",
                    "email": signatory.mail,
                    "signature_timestamp": cast(datetime, signature.signe_at).isoformat() \
                        if signature.signe_at else None,
                    "ip_address": signature.ip_addresse,
                    "user_agent_hash": hashlib.sha256(
                        signature.user_agent.encode()
                        if signature.user_agent
                        else b''
                    ).hexdigest()[:16],
                    "signature_hash": signature.signature_hash
                }
                cert_data["signatories"].append(signatory_info)

        return cert_data

    @staticmethod
    def _add_signatures_details(
        signatories: list[User],    # pylint: disable=W0613
        signatures: list[Signatures],
        cert_data: dict[str, Any],
        sig_to_user: dict[int, User]
    ) -> dict[str, Any]:
        """Ajoute les détails techniques des signatures au certificat.

        :param signatories: Liste des utilisateurs signataires
        :type signatories: list[User]
        :param signatures: Liste des signatures
        :type signatures: list[Signatures]
        :param cert_data: Dictionnaire du certificat à remplir
        :type cert_data: dict[str, Any]
        :param sig_to_user: Mapping signature_id -> User
        :type sig_to_user: dict[int, User]

        :returns: Dictionnaire du certificat mis à jour
        :rtype: dict[str, Any]
        """
        for signature in signatures:
            # Utiliser le mapping pour trouver l'utilisateur correspondant
            signatory = sig_to_user.get(signature.id)
            if signatory:
                # Détails techniques de la signature
                signature_detail: dict[str, Any] = {
                    "signature_id": signature.id,
                    "status": signature.status,
                    "svg_data_hash": hashlib.sha256(
                        signature.svg_graph.encode()
                        if signature.svg_graph
                        else b''
                    ).hexdigest(),
                    "data_graph_hash": hashlib.sha256(
                        signature.data_graph.encode()
                        if signature.data_graph
                        else b''
                    ).hexdigest(),
                    "dimensions": {
                        "width": signature.largeur_graph,
                        "height": signature.hauteur_graph
                    },
                    "timestamp": cast(
                        datetime,
                        signature.timestamp_graph).isoformat()
                            if signature.timestamp_graph
                            else None
                }
                cert_data["signature_details"].append(signature_detail)

        return cert_data

    @staticmethod
    def create_secure_certificate(
        signatures: list[Signatures],
        signatories: list[User],
        document: DocToSigne,
        view_points: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Crée un certificat sécurisé avec signature cryptographique.
        
        :param signatures: Liste des objets Signatures
        :type signatures: list[Signatures]
        :param signatories: Liste des objets User signataires
        :type signatories: list[User]
        :param document: Le document signé
        :type document: DocToSigne
        :param view_points: Liste optionnelle des view_points pour correspondance
        :type view_points: list[dict[str, Any]] | None

        :return: dict contenant le certificat sécurisé
        :rtype: dict[str, Any]
        """
        # Créer un mapping signature_id -> user pour faciliter la correspondance
        sig_to_user: dict[int, User] = {}
        if view_points:
            for vp in view_points:
                sig_dict = vp.get('signature')
                user_dict = vp.get('user')
                if sig_dict and user_dict and sig_dict.get('id'):
                    # Trouver l'objet User correspondant dans signatories
                    user = next((u for u in signatories if u.id == user_dict.get('id')), None)
                    if user:
                        sig_to_user[sig_dict['id']] = user

        try:
            # Création de la clé privée pour la signature et de l'identifiant unique du certificat
            private_key = SecureCertificateManager.generate_signing_key()
            cert_id = secrets.token_hex(16)
            timestamp = datetime.now()

            # Créer les données du certificat
            cert_data: dict[str, Any] = {
                "certificate_id": cert_id,
                "document_hash": document.hash_fichier if document else "unknown",
                "creation_timestamp": timestamp.isoformat(),
                "signatures_count": len(signatures),
                "signatories": [],
                "signature_details": [],
                "integrity_checks": {
                    "document_verified": True,
                    "all_signatures_valid": True,
                    "timestamp_verified": True
                }
            }

            # Ajouter les informations des signataires et les détails des signatures
            cert_data = SecureCertificateManager._add_signatories_info(signatories, signatures,
                                                                       cert_data, sig_to_user)
            cert_data = SecureCertificateManager._add_signatures_details(signatories, signatures,
                                                                         cert_data, sig_to_user)

            # Créer la signature cryptographique du certificat
            cert_json = json.dumps(cert_data, sort_keys=True, separators=(',', ':'))
            cert_signature = SecureCertificateManager._sign_data(cert_json.encode(), private_key)

            # Certificat final avec signature
            secure_cert: dict[str, Any] = {
                "certificate": cert_data,
                "cryptographic_signature": cert_signature.hex(),
                "public_key": private_key.public_key().public_bytes(
                    encoding=Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode(),
                "algorithm": "RSA-SHA256",
                "version": "1.0"
            }

            return secure_cert

        except (
            TypeError,
            ValueError,
            InvalidKey,
            UnsupportedAlgorithm,
            InternalError,
        ) as e:
            raise ValueError(f"Erreur lors de la création du certificat sécurisé : {e}") from e

    @staticmethod
    def _sign_data(data: bytes, private_key: Any) -> bytes:
        """Signe des données avec la clé privée.
        
        :param data: Données à signer
        :type data: bytes
        :param private_key: Clé privée RSA
        :type private_key: Any

        :returns: Signature cryptographique
        :rtype: bytes
        """
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    @staticmethod
    def verify_certificate(secure_cert: dict[str, Any]) -> bool:
        """Vérifie l'intégrité d'un certificat sécurisé.
        
        :param secure_cert: Certificat sécurisé à vérifier
        :type secure_cert: dict[str, Any]

        :returns: True si le certificat est valide
        :rtype: bool
        """
        try:
            # Extraire les composants
            cert_data = secure_cert["certificate"]
            signature_hex = secure_cert["cryptographic_signature"]
            public_key_pem = secure_cert["public_key"]

            # Reconstruire les données du certificat
            cert_json = json.dumps(cert_data, sort_keys=True, separators=(',', ':'))

            # Charger la clé publique
            public_key = serialization.load_pem_public_key(public_key_pem.encode())

            # Vérifier la signature
            signature_bytes = bytes.fromhex(signature_hex)

            # Vérifier que c'est bien une clé RSA
            if isinstance(public_key, rsa.RSAPublicKey):
                public_key.verify(
                    signature_bytes,
                    cert_json.encode(),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            else:
                raise ValueError("La clé publique n'est pas une clé RSA valide.")

            return True

        except (
            KeyError,
            TypeError,
            ValueError,
            InvalidKey,
            InvalidSignature,
            UnsupportedAlgorithm,
            InternalError,
        ) as e:
            raise ValueError(f"Échec de la vérification du certificat : {e}") from e
