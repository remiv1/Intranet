"""Module pour la gestion de l'objet de création de signature

.. classes::
    - `SignatureDoer`: Classe responsable de la gestion de la création de signatures.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.1.0
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from flask import Request, session, g

from ..models import DocToSigne, Invitation, Points, Signatures

BAD_INVITATION = 'Invitation invalide ou non trouvée.'

class SignatureDoer:
    """
    Gère le processus de signature d'un document.
    TODO : Prévoir de créer des dataclass
    Attributes:
        request (Request): L'objet request Flask.
        signatory_id (int | None): L'ID de l'utilisateur signataire.
        document (DocToSigne | None): Le document à signer.
        invitation (Invitation | None): L'invitation associée au document et à l'utilisateur.
        token (str | None): Le token d'invitation.
        ip_addresse (str | None): L'adresse IP de l'utilisateur.
        otp (str | None): Le code OTP soumis par l'utilisateur.
        signature_hash (str | None): Le hash de la signature soumise.
        user_agent (str | None): Le User-Agent de l'utilisateur.
        svg_graph (str | None): Le SVG de la signature graphique.
        data_graph (str | None): Les données brutes de la signature graphique.
        largeur_graph (int): La largeur du graphique de signature.
        hauteur_graph (int): La hauteur du graphique de signature.
        datetime_submission (datetime | None): La date et l'heure de la soumission de la signature.
        object_points (List[Points]): Liste des objets Points récupérés depuis la base.
        points (List[Dict[str, Any]]): Liste des points de signature sous forme de dictionnaires.
    Methods:
        get_request(id_document: int, hash_document: str):
            Récupère les données de la requête.
        post_request(id_document: int, hash_document: str):
            Traite la soumission du formulaire de signature.
        get_signature_points():
            Récupère les points de signature pour l'utilisateur courant et la signature demandée.
        handle_signature_submission():
            Gère la soumission de la signature.
    """
    def __init__(self, req: Request):
        """
        Initialise avec l'objet request Flask.
        Args:
            req (Request): L'objet request Flask.
        Attributes:
            request (Request): L'objet request Flask.
            signatory_id (int | None): L'ID de l'utilisateur signataire.
            document (DocToSigne | None): Le document à signer.
            invitation (Invitation | None): L'invitation associée au document et à l'utilisateur.
            token (str | None): Le token d'invitation.
        Exemples:
            ```python
            doer = SignatureDoer(request)
            ```
        """
        self.request = req
        self.token = None
        self.signatory_id = None
        self.signatory_name = None
        self.invitation = None
        self.document = None
        self.ip_addresse = None
        self.otp = None
        self.signature_hash = None
        self.user_agent = None
        self.svg_graph = None
        self.data_graph = None
        self.largeur_graph = 0
        self.hauteur_graph = 0
        self.datetime_submission = None
        self.object_points: list[Points] = []
        self.points: list[dict[str, Any]] = []
        self.old_name = None
        self.new_name = None
        self.type = None
        self.subtype = None
        self.priority = None
        self.signing_deadline = None
        self.validity = None
        self.description = None
        self.doc_to_signe: DocToSigne | None = None
        self.limite_signature = None

    def get_request(self, *, id_document: int, hash_document: str) -> 'SignatureDoer':
        """
        Récupère les données de la requête de type GET.
        Args:
            id_document (int): L'ID du document à signer.
            hash_document (str): Le hash du document à signer.
        Returns:
            self: SignatureDoer
        Raises:
            ValueError: Si le document ou l'invitation n'est pas trouvé ou invalide
        Exemples:
            ```python
            doer = SignatureDoer(request).get_request()
            ```
        """
        # Récupération des paramètres de la requête
        self.token = self.request.args.get('token', None)

        # Récupération de l'utilisateur courant
        self.signatory_id = int(session.get('id', None))
        self.signatory_name = f'{session.get("prenom", None)} {session.get("nom", None)}'.strip()

        # Validation de l'invitation et du document :
        # Le document doit exister et correspondre au hash fourni
        document = g.db_session.query(DocToSigne) \
                        .filter_by(id=id_document, hash_fichier=hash_document) \
                        .first()
        # Existance invitation, utilisateur, token
        invitation = g.db_session.query(Invitation) \
                        .filter_by(id_document=document.id, id_user=self.signatory_id) \
                        .first()

        # Si le document ou l'invitation n'est pas trouvé ou invalide, lever une erreur
        if invitation and invitation.token == self.token and document:
            self.invitation = invitation
            self.document = document
        else:
            raise ValueError(BAD_INVITATION)
        return self

    def post_request(self, *, id_document: int, hash_document: str) -> 'SignatureDoer':
        """
        Traite la soumission du formulaire de signature de type POST.
        Args:
            id_document (int): L'ID du document à signer.
            hash_document (str): Le hash du document à signer.
        Returns:
            self: SignatureDoer
        Raises:
            ValueError: Si le document ou l'invitation n'est pas trouvé ou invalide
        Exemples:
            ```python
            doer = SignatureDoer(request).post_request(id_document=1, hash_document='abc123')
            ```
        """
        # Récupération des données de la requête
        self.token = self.request.headers.get('X-Invit-Token', None)
        self.ip_addresse = self.request.environ.get('REMOTE_ADDR') or self.request.remote_addr
        data = self.request.get_json()

        # Validation des données reçues
        if not data:
            raise ValueError("Données de signatures invalides ou manquantes.")
        self.otp = data.get('otp_code', None)

        # Données de signature haute précision
        self.signature_hash = data.get('signature_hash', None)
        self.user_agent = data.get('user_agent', None)
        self.svg_graph = data.get('svg_graph', None)
        self.data_graph = data.get('data_graph', None)
        self.largeur_graph = data.get('largeur_graph', 0)
        self.hauteur_graph = data.get('hauteur_graph', 0)

        # Données temporelles et d'identité
        self.datetime_submission = datetime.now()
        self.signatory_id = session.get('id', None)

        # Récupération des documents et invitations correspondants
        self.document = g.db_session.query(DocToSigne) \
            .filter_by(id=id_document, hash_fichier=hash_document) \
            .first()
        self.invitation = g.db_session.query(Invitation) \
            .filter_by(id_document=self.document.id, id_user=self.signatory_id) \
            .first()

        return self

    def get_signature_points(self) -> 'SignatureDoer':
        """
        Récupère les points de signature pour l'utilisateur courant et la signature demandée.
        Args:
            self: SignatureDoer
        Returns:
            self: SignatureDoer
        Exemples:
            ```python
            doer = SignatureDoer(request) \
                        .get_request(id_document=1, hash_document='abc123') \
                        .get_signature_points()

            # Situation POST
            doer = SignatureDoer(request) \
                        .post_request(id_document=1, hash_document='abc123') \
                        .get_signature_points()
            ```
        """
        # Récupération des points de signature pour l'utilisateur courant
        if not self.document:
            raise ValueError("Document non trouvé pour récupérer les points de signature.")
        self.object_points = g.db_session.query(Points) \
                        .filter_by(id_document=self.document.id, id_user=self.signatory_id) \
                        .all()
        self.points: List[Dict[str, Any]] = [point.to_dict() for point in self.object_points]

        return self

    def handle_signature_submission(self) -> 'SignatureDoer':
        """
        Gère la soumission de la signature.
        Args:
            self: SignatureDoer
        Returns:
            self: SignatureDoer
        Raises:
            ValueError: Si la signature est invalide ou si l'utilisateur a déjà signé.
        Exemples:
            ```python
            doer = SignatureDoer(request) \
                .post_request(id_document=1, hash_document='abc123') \
                .get_signature_points() \
                .handle_signature_submission()
            ```
        """
        # Validation de l'invitation, du document et du code OTP
        if not self.invitation:
            raise ValueError(BAD_INVITATION)
        otp_valid = self.otp == self.invitation.code_otp

        # Validation des conditions de signature
        if not self.object_points:
            raise ValueError("Aucun pt de signature trouvé pour cet utilisateur et ce document.")
        already_signed = all(point.status == 1 for point in self.object_points)
        if already_signed:
            raise ValueError("Vous avez déjà signé ce document.")
        if self.invitation.expire_at < datetime.now():
            raise ValueError("L'invitation a expiré.")
        if not self.document or not self.invitation or not self.points or not otp_valid:
            raise ValueError(BAD_INVITATION)

        # Création de l'entrée dans la table Signatures
        signature: Signatures = Signatures(
            signe_at=self.datetime_submission,
            signature_hash=self.signature_hash or 'unknown',
            ip_addresse=self.ip_addresse,
            user_agent=self.user_agent or self.request.headers.get('User-Agent', 'unknown'),
            status=1,  # Statut signé
            svg_graph=self.svg_graph,
            data_graph=self.data_graph,
            largeur_graph=self.largeur_graph,
            hauteur_graph=self.hauteur_graph,
            timestamp_graph=self.datetime_submission,
        )
        g.db_session.add(signature)
        g.db_session.flush()

        # Mise à jour des points de signature de l'utilisateur courant
        for point in self.object_points:
            point.status = 1  # Statut signé
            point.signe_at = self.datetime_submission or datetime.now()
            point.id_signature = signature.id

        # Vérifier si tous les points du document sont maintenant signés
        all_points = g.db_session.query(Points).filter_by(id_document=self.document.id).all()
        all_signed = all(p.status == 1 for p in all_points)

        if all_signed:
            # Tous les signataires ont signé, marquer le document comme complètement signé
            self.document.status = 1  # Statut signé
            self.document.complete_at = self.datetime_submission
        else:
            # Il reste des signatures en attente
            if self.document.status != 0:
                self.document.status = 0  # Statut en attente

        return self
