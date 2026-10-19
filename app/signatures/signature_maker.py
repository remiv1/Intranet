"""Module for creating and managing signatures.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

import shutil
import hashlib
import hmac
from typing import Any
from os import getenv
from pathlib import Path
from datetime import datetime, timedelta

from flask import Request, session, g, render_template, request

from . import SecureDocumentAccess
from .utils import send_email_invitation
from ..models import DocToSigne, Points, User, Invitation

DEFAULT_TEMP_DIR = getenv('DEFAULT_TEMP_DIR', '/tmp/')

class SignatureMaker:
    """Classe pour gérer la création de documents à signer.

    :param request: L'objet request Flask.
    :type request: Request
    :param old_name: Le nom original du document.
    :type old_name: str | None
    :param new_name: Le nouveau nom du document.
    :type new_name: str | None
    :param type: Le type de document.
    :type type: str | None
    :param subtype: Le sous-type de document.
    :type subtype: str | None
    :param priority: La priorité du document.
    :type priority: str | None
    :param signing_deadline: La date limite de signature.
    :type signing_deadline: str | None
    :param validity: La durée de validité du document.
    :type validity: str | None
    :param description: La description du document.
    :type description: str | None
    :param points: Liste des points de signature.
    :type points: list[Dict[str, Any]]
    :param doc_to_signe: Le document à signer créé.
    :type doc_to_signe: DocToSigne | None
    :param limite_signature: La date limite pour la signature.
    :type limite_signature: datetime | None

    .. methods::
        - `get_request(request: Request)`: Récupère les données du formulaire de la requête.
        - `get_signature_points()`: Récupère les points de signature du formulaire de la requête.
        - `create_document()`: Crée un document à signer.
        - `create_points()`: Crée les points de signature dans la base de données.
        - `fix_documents()`: Renomme le document dans le dossier temporaire vers le dossier final.
        - `send_invitation()`: Envoie une invitation aux utilisateurs pour signer le document.

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    def __init__(self, req: Request):
        """Initialise avec l'objet request Flask.

        :param req: L'objet request Flask.
        :type req: Request
        
        .. exemple::
            .. code-block:: python
            maker = SignatureMaker(request)
        """
        self.request = req
        self.old_name = None
        self.new_name = None
        self.type = None
        self.subtype = None
        self.priority = None
        self.signing_deadline = None
        self.validity = None
        self.description = None
        self.points = []
        self.limite_signature = None
        self.doc_to_signe: DocToSigne = DocToSigne()

    def post_request(self) -> 'SignatureMaker':
        """Récupère les données du formulaire de la requête POST.

        :return: self
        :rtype: SignatureMaker

        .. exemple::
            .. code-block:: python
            maker = SignatureMaker(request).post_request()
        """
        # Récupération des données du formulaire
        self.old_name = self.request.form.get('doc_id', None)
        self.new_name = self.request.form.get('document_name', None) or self.old_name
        self.type = self.request.form.get('document_type', None)
        self.subtype = self.request.form.get('document_subtype', None)
        self.priority = self.request.form.get('document_priority', None)
        self.signing_deadline = self.request.form.get('signing_deadline', None)
        self.validity = self.request.form.get('document_validity', None)
        self.description = self.request.form.get('document_description', None)

        return self

    def get_signature_points(self) -> 'SignatureMaker':
        """Récupère les points de signature du formulaire de la requête.
        
        :return: self
        :rtype: SignatureMaker

        .. exemple::
            .. code-block:: python
                maker = SignatureMaker(request) \
                    .post_request() \
                    .get_signature_points()
        """
        # Création de la liste des points de signature
        self.points: list[dict[str, Any]] = []
        i = 0

        # Boucle pour récupérer les points de signature
        while f'signature_points[{i}][x]' in self.request.form:
            # Création du dictionnaire pour chaque point
            point: dict[str, float | int] = {
                'x': float(self.request.form.get(f'signature_points[{i}][x]', 0)),
                'y': float(self.request.form.get(f'signature_points[{i}][y]', 0)),
                'page_num': int(self.request.form.get(f'signature_points[{i}][pageNum]', 1)),
                'user_id': int(self.request.form.get(f'signature_points[{i}][user_id]', 1)),
            }

            # Ajout du point à la liste
            self.points.append(point)

            # Incrémentation de l'index
            i += 1

        return self

    def create_document(self) -> 'SignatureMaker':
        """Crée un document à signer.

        :return: self
        :rtype: SignatureMaker

        .. exemple::
            .. code-block:: python
            maker = SignatureMaker(request) \
                .post_request() \
                .get_signature_points() \
                .create_document()
            ```
        """
        # Création du document à signer dans la base de données par l'ORM
        self.doc_to_signe: DocToSigne = DocToSigne(
            doc_nom=self.new_name,
            doc_type=self.type,
            doc_sous_type=self.subtype,
            priorite=int(self.priority) if self.priority and self.priority.isdigit() else 0,
            echeance=self.signing_deadline,
            duree_archivage=int(self.validity) \
                                if self.validity and self.validity.isdigit() else 3660,
            description=self.description,
            chemin_fichier='temp',  # Sera mis à jour après le renommage
            hash_fichier='temp',    # Sera mis à jour après le renommage
            id_user=session.get('id', 0),
        )

        # Ajout du document à la session et flush pour obtenir l'ID
        g.db_session.add(self.doc_to_signe)
        g.db_session.flush()

        return self

    def create_points(self) -> 'SignatureMaker':
        """Crée les points de signature dans la base de données.

        :return: self
        :rtype: SignatureMaker

        .. exemple::
            .. code-block:: python
            maker = SignatureMaker(request) \
                .post_request() \
                .get_signature_points() \
                .create_document() \
                .create_points()
            ```
        """
        # Création des points de signature dans la base de données par l'ORM par boucle
        for point in self.points:
            signature_point: Points = Points(
                id_document=self.doc_to_signe.id,
                id_user=point['user_id'],
                page_num=point['page_num'],
                x=point['x'],
                y=point['y']
            )

            # Ajout du point à la session
            g.db_session.add(signature_point)

        return self

    def fix_documents(self) -> 'SignatureMaker':
        """Renomme le document dans le dossier temporaire vers le dossier final.

        :return: self
        :rtype: SignatureMaker

        :raises FileNotFoundError: Si le fichier source n'existe pas.
        :raises IOError: Si une erreur survient lors du renommage du fichier.

        .. exemple::
            .. code-block:: python
            maker = SignatureMaker(request) \
                .post_request() \
                .get_signature_points() \
                .create_document() \
                .create_points() \
                .fix_documents()
            ```
        """
        # Renommage du fichier dans le dossier temporaire vers le dossier final
        if self.old_name and self.new_name:
            # Définition des chemins
            temp_dir = SecureDocumentAccess.TEMP_DIR
            final_dir = getenv(
                'SIGNATURE_DOCKER_PATH', DEFAULT_TEMP_DIR
            ) + f'/{self.doc_to_signe.id}/'
            Path(final_dir).mkdir(parents=True, exist_ok=True)
            old_path = Path(temp_dir) / self.old_name
            new_path = Path(final_dir) / self.new_name

            # Vérification de l'existence du fichier source
            if old_path.exists():
                try:
                    # Déplacement du fichier vers le nouveau chemin
                    file_path = shutil.move(str(old_path), str(new_path))

                    # Calcul du hash SHA-256 du fichier déplacé
                    with open(new_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        self.doc_to_signe.chemin_fichier = file_path
                        self.doc_to_signe.hash_fichier = file_hash

                    return self

                # Gestion des erreurs lors du renommage
                except Exception as e:
                    raise IOError(f"Erreur lors du renommage du fichier : {e}") from e

            # Gestion des exceptions liées à l'absence du fichier source
            else:
                raise FileNotFoundError("Le fichier source n'existe pas.")

        # Gestion des exceptions liées à l'absence de noms valides
        raise FileNotFoundError("Le fichier source n'existe pas ou les noms sont invalides.")

    def send_invitation(self) -> 'SignatureMaker':
        """Envoie une invitation aux utilisateurs pour signer le document.

        :return: self
        :rtype: SignatureMaker

        .. exemple::
            .. code-block:: python
            maker = SignatureMaker(request) \
                .post_request() \
                .get_signature_points() \
                .create_document() \
                .create_points() \
                .fix_documents() \
                .send_invitation()
            ```
        """
        # Récupération de la liste des mails, noms et prénoms des utilisateurs
        user_ids = {point['user_id'] for point in self.points}
        users = g.db_session.query(User).filter(User.id.in_(user_ids)).all()
        self.limite_signature = datetime.now() \
            + timedelta(days=int(self.doc_to_signe.echeance) \
            if self.doc_to_signe.echeance \
                and str(self.doc_to_signe.echeance).isdigit() else 3)

        # Envoi des invitations par email
        for user in users:
            # Vérifier si une invitation existe déjà pour ce document et cet utilisateur
            existing_invitation = g.db_session.query(Invitation).filter_by(
                id_document=self.doc_to_signe.id,
                id_user=user.id
            ).first()

            # Si une invitation existe, la mettre à jour, sinon en créer une nouvelle
            if existing_invitation:
                # Mettre à jour l'invitation existante
                invitation = existing_invitation
                invitation.expire_at = self.limite_signature
                invitation.mail_envoye = True
                invitation.mail_compte += 1
            else:
                # Générer un token unique pour chaque utilisateur
                user_token = hmac.new(
                    getenv('SECRET_KEY', 'default-secret-key').encode(),
                    f"{self.doc_to_signe.id}-{self.doc_to_signe.hash_fichier}".encode() +
                    f"-{user.id}-{datetime.now().isoformat()}".encode(),
                    hashlib.sha256
                ).hexdigest()

                # Création d'une nouvelle invitation
                invitation = Invitation(
                    id_document=self.doc_to_signe.id,
                    id_user=user.id,
                    token=user_token,
                    expire_at=self.limite_signature,
                    mail_envoye=True,
                    mail_compte=1
                )
                g.db_session.add(invitation)
                g.db_session.flush()

            # Envoyer l'email
            mail_template = render_template(
                'signatures/signature_mail.html',
                nom_expediteur=f'{session.get("prenom", "")} {session.get("nom", "")}'.strip(),
                nom_signataire=f'{user.prenom} {user.nom}'.strip(),
                doc_titre=self.doc_to_signe.doc_nom,
                doc_type=self.doc_to_signe.doc_type,
                date_limite=self.limite_signature.strftime('%d/%m/%Y %H:%M'),
                lien_signature=(
                    f"{request.url_root.rstrip('/')}/signature/signer/" +
                    f"{self.doc_to_signe.id}/{self.doc_to_signe.hash_fichier}?" +
                    f"token={invitation.token}"
                )
            )
            send_email_invitation(
                to=user.mail,
                template=mail_template
            )

        return self
