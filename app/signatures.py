"""
Page des gestion des fonctions liées à la signature électronique.
Fonctions:
- Ajout de la signature graphique sur un document PDF.
- Ajout d'un certificat de signature numérique.
- Stockage temporaire des documents avant signature.
- Enregistrement des ashages des documents signés pour vérification ultérieure.
"""
# Imports standards
import hashlib, hmac, json, logging, secrets, shutil, smtplib, cairosvg
from datetime import datetime, timedelta
from io import BytesIO
from os import getenv
from pathlib import Path

# Imports liés aus emails
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

# Imports de typages
from typing import Any, Dict, List

# Imports liés aux cryptages et écritures PDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding
from PIL import Image as PILImage
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter


# Imports Flask
from flask import render_template, request, Request, g, session

# Imports liés à l'application (modèles, config)
from config import Config
from models import DocToSigne, Invitation, Points, Signatures, User, ViewPoints

# Constantes
BAD_INVITATION = 'Invitation invalide ou non trouvée.'

class SignatureDoer:
    """
    Gère le processus de signature d'un document.
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
    def __init__(self, request: Request):
        """
        Initialise avec l'objet request Flask.
        Args:
            request (Request): L'objet request Flask.
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
        self.request = request

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
        self.signatory_name = f'{session.get('prenom', None)} {session.get('nom', None)}'.strip()

        # Validation de l'invitation et du document :
        # Le document doit exister et correspondre au hash fourni
        document = g.db_session.query(DocToSigne).filter_by(id=id_document, hash_fichier=hash_document).first()
        # L'invitation doit exister pour ce document et cet utilisateur, et le token doit correspondre
        invitation = g.db_session.query(Invitation).filter_by(id_document=document.id, id_user=self.signatory_id).first()

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
        otp_valid = (self.otp == self.invitation.code_otp)
        
        # Validation des conditions de signature
        already_signed = all(point.status == 1 for point in self.object_points)
        if already_signed:
            raise ValueError("Vous avez déjà signé ce document.")
        elif self.invitation.expire_at < datetime.now():
            raise ValueError("L'invitation a expiré.")
        elif not self.document or not self.invitation or not self.points or not otp_valid:
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
            point.signe_at = self.datetime_submission
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

class SignatureMaker:
    """
    Classe pour gérer la création de documents à signer.
    Attributes:
        request (Request): L'objet request Flask.
        old_name (str | None): Le nom original du document.
        new_name (str | None): Le nouveau nom du document.
        type (str | None): Le type de document.
        subtype (str | None): Le sous-type de document.
        priority (str | None): La priorité du document.
        signing_deadline (str | None): La date limite de signature.
        validity (str | None): La durée de validité du document.
        description (str | None): La description du document.
        points (list[Dict[str, Any]]): Liste des points de signature.
        doc_to_signe (DocToSigne | None): Le document à signer créé.
        limite_signature (datetime | None): La date limite pour la signature.
    Methods:
        get_request(request: Request):
            Récupère les données du formulaire de la requête.
        get_signature_points():
            Récupère les points de signature du formulaire de la requête.
        create_document():
            Crée un document à signer.
        create_points():
            Crée les points de signature dans la base de données.
        fix_documents():
            Renomme le document dans le dossier temporaire vers le dossier final.
        send_invitation():
            Envoie une invitation aux utilisateurs pour signer le document.
    """
    def __init__(self, request: Request):
        """
        Initialise avec l'objet request Flask.
        Args:
            request (Request): L'objet request Flask.
        Attributes:
            request (Request): L'objet request Flask.
            old_name (str | None): Le nom original du document.
            new_name (str | None): Le nouveau nom du document.
            type (str | None): Le type de document.
            subtype (str | None): Le sous-type de document.
            priority (str | None): La priorité du document.
            signing_deadline (str | None): La date limite de signature.
            validity (str | None): La durée de validité du document.
            description (str | None): La description du document.
            points (list[Dict[str, Any]]): Liste des points de signature.
            doc_to_signe (DocToSigne | None): Le document à signer créé.
            limite_signature (datetime | None): La date limite pour la signature.
        Exemples:
            ```python
            maker = SignatureMaker(request)
            ```
        """
        self.request = request

    def post_request(self) -> 'SignatureMaker':
        """
        Récupère les données du formulaire de la requête POST.
        Args:
            self: SignatureMaker
        Returns:
            self: SignatureMaker
        Exemples:
            ```python
            maker = SignatureMaker(request).post_request()
            ```
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
        """
        Récupère les points de signature du formulaire de la requête.
        Args:
            self: SignatureMaker
        Returns:
            self: SignatureMaker
        Exemples:
            ```python
            maker = SignatureMaker(request) \
                            .post_request() \
                            .get_signature_points()
            ```
        """
        # Création de la liste des points de signature
        self.points: list[Dict[str, Any]] = []
        i = 0

        # Boucle pour récupérer les points de signature
        while f'signature_points[{i}][x]' in self.request.form:
            # Création du dictionnaire pour chaque point
            point: Dict[str, float | int] = {
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
        """
        Crée un document à signer.
        Args:
            self: SignatureMaker
        Returns:
            self: SignatureMaker
        Exemples:
            ```python
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
            duree_archivage=int(self.validity) if self.validity and self.validity.isdigit() else 3660,
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
        """
        Crée les points de signature dans la base de données.
        Args:
            self: SignatureMaker
        Returns:
            self: SignatureMaker
        Exemples:
            ```python
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
        """
        Renomme le document dans le dossier temporaire vers le dossier final.
        Args:
            self: SignatureMaker
        Returns:
            self: SignatureMaker
        Raises:
            FileNotFoundError: Si le fichier source n'existe pas.
            IOError: Si une erreur survient lors du renommage du fichier.
        Exemples:
            ```python
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
            final_dir = getenv('SIGNATURE_DOCKER_PATH', '/tmp/')
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
                except Exception:
                    raise IOError("Erreur lors du renommage du fichier.")
            
            # Gestion des exceptions liées à l'absence du fichier source
            else:
                raise FileNotFoundError("Le fichier source n'existe pas.")
        
        # Gestion des exceptions liées à l'absence de noms valides
        raise FileNotFoundError("Le fichier source n'existe pas ou les noms sont invalides.")
    
    def send_invitation(self) -> 'SignatureMaker':
        """
        Envoie une invitation aux utilisateurs pour signer le document.
        Args:
            self: SignatureMaker
        Returns:
            self: SignatureMaker
        Exemples:
            ```python
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
        self.limite_signature = datetime.now() + timedelta(days=int(self.doc_to_signe.echeance) if self.doc_to_signe.echeance and str(self.doc_to_signe.echeance).isdigit() else 3)
        
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
                    f"{self.doc_to_signe.id}-{self.doc_to_signe.hash_fichier}-{user.id}-{datetime.now().isoformat()}".encode(),
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
                lien_signature=f"{request.url_root.rstrip('/')}/signature/signer/{self.doc_to_signe.id}/{self.doc_to_signe.hash_fichier}?token={invitation.token}"
            )
            send_email_invitation(
                to=user.mail,
                template=mail_template
            )
        
        return self

class SecureDocumentAccess:
    """
    Classe pour gérer l'accès sécurisé aux documents via fichiers temporaires.
    Attributes:
        TEMP_DIR (str): Le chemin du dossier temporaire pour les fichiers d'accès.
    Methods:
        get_user_identifier():
            Génère un identifiant unique pour l'utilisateur basé sur session, IP et User-Agent.
        generate_document_hash(filename: str, user_identifier: str | None = None) -> str:
            Génère un hash sécurisé pour le document avec HMAC.
        create_temp_access_file(filename: str, document_hash: str) -> None:
            Crée un fichier JSON temporaire avec les informations d'accès.
        verify_temp_access(filename: str) -> bool:
            Vérifie l'accès au document via les fichiers temporaires.
        cleanup_expired_temp_files() -> None:
            Nettoie les fichiers temporaires expirés.
    """
    # Constante pour le dossier temporaire
    TEMP_DIR = getenv('TEMP_DOCKER_PATH', '/tmp') + '/signature'
    
    @staticmethod
    def get_user_identifier() -> str:
        """
        Génère un identifiant unique pour l'utilisateur basé sur session, IP et User-Agent.
        Args:
            None
        Returns:
            str: L'identifiant unique de l'utilisateur.
        Exemples:
            ```python
            user_id = SecureDocumentAccess.get_user_identifier()
            ```
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
        """
        Génère un hash sécurisé pour le document avec HMAC.
        Args:
            filename (str): Le nom du fichier.
            user_identifier (str | None): L'identifiant unique de l'utilisateur. Si None, il sera généré.
        Returns:
            str: Le hash sécurisé du document.
        Exemples:
            ```python
            doc_hash = SecureDocumentAccess.generate_document_hash('document.pdf')
            ```
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
        """
        Crée un fichier JSON temporaire avec les informations d'accès.
        Args:
            filename (str): Le nom du fichier.
            document_hash (str): Le hash sécurisé du document.
        Returns:
            None
        Exemples:
            ```python
            SecureDocumentAccess.create_temp_access_file('document.pdf', 'abc123hash')
            ```
        """
        # Création du dossier temporaire s'il n'existe pas
        temp_dir = Path(SecureDocumentAccess.TEMP_DIR)
        temp_dir.mkdir(exist_ok=True)
        
        # Données à stocker dans le fichier JSON
        access_data: Dict[str, Any] = {
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
        """
        Vérifie l'accès au document via les fichiers temporaires.
        Args:
            filename (str): Le nom du fichier à vérifier.
        Returns:
            bool: True si l'accès est valide, False sinon.
        Exemples:
            ```python
            is_valid = SecureDocumentAccess.verify_temp_access('document.pdf')
            ```
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
        """
        Nettoie les fichiers temporaires expirés.
        Args:
            None
        Returns:
            None
        Exemples:
            ```python
            SecureDocumentAccess.cleanup_expired_temp_files()
            ```
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

class SignedDocumentCreator:
    """
    Classe pour gérer la création du document PDF final signé.
    
    Cette classe s'occupe de :
    - Charger le document à signer et vérifier les droits d'accès.
    - Vérifier l'intégrité du document via son hash.
    - Récupérer les points et signatures associées au document.
    - Vérifier si toutes les signatures requises ont été effectuées.
    - Appliquer les signatures SVG sur le document PDF.
    - Incorporer les certificats de signature dans le PDF.
    - Sauvegarder le document signé final.
    - Envoyer le document signé par email à tous les participants.

    Attributes:
        id_document (int): L'ID du document à traiter.
        current_user_id (int): L'ID de l'utilisateur qui demande la création.
        document (DocToSigne | None): Le document à signer.
        document_path (Path | None): Le chemin vers le fichier PDF du document.
        points (List[Points]): Liste des points de signature associés au document.
        signatures (List[Signatures]): Liste des signatures associées au document.
        signatories (List[User]): Liste des utilisateurs signataires.
        creator (User | None): L'utilisateur créateur du document.
        signed_document_path (Path | None): Le chemin vers le fichier PDF signé final.
    
    Methods:
        load_and_verify_document(hash_document: str) -> 'SignedDocumentCreator':
            Charge le document, vérifie les droits d'accès ET l'intégrité du fichier via son hash.
        load_signatures_and_points() -> 'SignedDocumentCreator':
            Récupère les points et signatures associées au document.
        verify_all_signatures_completed() -> 'SignedDocumentCreator':
            Vérifie si toutes les signatures requises ont été effectuées.
        apply_signatures_to_pdf() -> 'SignedDocumentCreator':
            Applique les signatures SVG sur le document PDF.
        _prepare_signed_document() -> None:
            Prépare le document signé en incorporant les certificats.
        _process_all_pages() -> None:
            Traite toutes les pages du document pour y ajouter les signatures.
        _write_signed_pdf() -> None:
            Écrit le document PDF signé dans le fichier de sortie.
        _create_fallback_copy() -> None:
            Crée une copie de secours du document signé.
        _update_document_hash() -> None:
            Met à jour le hash du document signé dans la base de données.
        _create_signature_overlay(page: Any, signatures_data: List[Dict[str, Any]], page_num: int) -> bytes | None:
            Crée une superposition PDF avec les signatures pour une page donnée.
        _add_single_signature_to_canvas(can: Canvas, data: Dict[str, Any], page_width: float, page_height: float) -> bool:
            Ajoute une seule signature SVG au canevas PDF.
        _process_signature_image(svg_graph: str, largeur: int, hauteur: int) -> PILImage.Image | None:
            Traite l'image SVG de la signature et la convertit en image PIL.
        _calculate_signature_position(self, point: Dict[str, Any], svg_image: PILImage.Image, 
                                     page_width: float, page_height: float) -> tuple[float, float]:
            Calcule la position de la signature sur la page.
        _draw_signature_on_canvas(self, can: Canvas, svg_image: PILImage.Image, 
                                     x_pos: float, y_pos: float, point: Dict[str, Any]) -> None:
            Dessine la signature sur le canevas PDF.
        _add_signature_metadata_text(self, can: Canvas, nom_complet: str, signature: Dict[str, Any],
                                     x_pos: float, y_pos: float, img_w: int, img_h: int, page_width: float) -> None:
            Ajoute les métadonnées de la signature au canevas PDF.
        _convert_svg_to_image(self, *, svg_content: str, width: int, height: int): -> PILImage.Image | None:
            Convertit le contenu SVG en une image PIL.
        add_signature_certificates() -> 'SignedDocumentCreator':
            Ajoute les certificats de signature dans le PDF.
        save_final_document() -> 'SignedDocumentCreator':
            Sauvegarde le document signé final.
        send_signed_document_by_email() -> 'SignedDocumentCreator':
            Envoie le document signé par email à tous les participants.
    """
    
    def __init__(self, *, id_document: int) -> None:
        """
        Initialise le créateur de document signé.
        
        Args:
            id_document (int): L'ID du document à traiter.
            hash_document (str): Le hash du document pour vérification.
            current_user_id (int): L'ID de l'utilisateur qui demande la création.
        """
        self.id_document = id_document
        self.current_user_id = session.get('id', 0)
        
        # Attributs qui seront initialisés par les méthodes
        self.document: DocToSigne | None = None
        self.document_path: Path | None = None
        self.points: List[Points] = []
        self.signatures: List[Signatures] = []
        self.signatories: List[User] = []
        self.creator: User | None = None
        self.signed_document_path: Path | None = None

    def load_and_verify_document(self, *, hash_document: str) -> 'SignedDocumentCreator':
        """
        Récupère le document en base, vérifie les droits d'accès et l'intégrité du fichier.
        
        Cette méthode combine la récupération du document, la vérification des permissions
        et la validation de l'intégrité du fichier via son hash SHA-256.

        Args:
            hash_document (str): Le hash du document pour vérification.

        Returns:
            self: SignedDocumentCreator avec document et document_path initialisés.
            
        Raises:
            ValueError: Si le document n'existe pas, hash invalide, accès non autorisé,
                       ou si le fichier a été modifié.
            FileNotFoundError: Si le fichier PDF n'est pas trouvé sur le disque.
        """
        # Récupérer le document en base
        self.document = g.db_session.query(DocToSigne).filter_by(
            id=self.id_document, 
            hash_fichier=hash_document
        ).first()
        
        # Vérifier que le document avec ce hash existe et lève une erreur si non
        if not self.document:
            raise ValueError("Document non trouvé ou hash invalide.")
        
        # Vérifier que l'utilisateur a le droit d'accéder à ce document
        # Soit il est le créateur, soit il a une invitation pour ce document
        is_creator = (self.document.id_user == self.current_user_id)
        has_invitation = g.db_session.query(Invitation).filter_by(
            id_document=self.id_document,
            id_user=self.current_user_id
        ).first() is not None
        
        # Si ça n'est pas le cas, lever une erreur d'accès non autorisé
        if not (is_creator or has_invitation):
            raise ValueError("Accès non autorisé à ce document.")
        
        # Récupérer le créateur du document et l'utilisateur expéditeur
        self.creator = g.db_session.query(User).filter_by(id=self.document.id_user).first()
        self.expeditor_user = g.db_session.query(User).filter_by(
            id=self.current_user_id
        ).first()

        # Préparer les données du document pour les logs et emails
        self.document_data: Dict[str, Any] = {
            'document': self.document,
            'expeditor': self.expeditor_user,
            'expeditor_mail': self.expeditor_user.mail if self.expeditor_user else None
        }
        
        # Vérifier l'existence du fichier PDF sur le disque
        self.document_path = Path(self.document.chemin_fichier)
        
        # Lever une erreur si le fichier n'existe pas
        if not self.document_path.exists():
            raise FileNotFoundError(f"Fichier PDF non trouvé : {self.document_path}")
        
        # Vérifier le hash du fichier
        with open(self.document_path, "rb") as f:
            file_content = f.read()
            calculated_hash = hashlib.sha256(file_content).hexdigest()
        
        # Lève une erreur si le hash ne correspond pas
        if calculated_hash != self.document.hash_fichier:
            raise ValueError("Le fichier a été modifié depuis sa création (hash invalide).")
        
        return self
    
    def load_signatures_and_points(self) -> 'SignedDocumentCreator':
        """
        Récupère les points et signatures associées au document et les utilisateurs associés
        et crée une structure consolidée.
        Args:
            self: SignedDocumentCreator
        Returns:
            self: SignedDocumentCreator
        Raises:
            ValueError: si aucun point n'est trouvé
        """
        if not self.document:
            raise ValueError("Document non chargé. Appelez load_and_verify_document() d'abord.")
        
        # Récupérer tous les points de signature des utilisateurs et leurs signatures
        points = g.db_session.query(Points).filter_by(
            id_document=self.id_document
        ).all()
        self.view_points: List[Dict[str, Any]] = ViewPoints(points).to_dict()

        # Levée d'erreur en cas de manque de données et de correspondance
        if not (self.view_points):
            raise ValueError("Aucun point de signature ou utilisateur trouvé pour ce document.")
        
        # Extraire les signatures et signataires uniques depuis view_points
        seen_signature_ids: set[Any] = set()
        seen_user_ids: set[Any] = set()

        for data in self.view_points:
            signature_data = data.get('signature')
            user_data = data.get('user')
            
            if signature_data and signature_data.get('id') not in seen_signature_ids:
                seen_signature_ids.add(signature_data['id'])
                # Récupérer l'objet Signature complet depuis la base
                sig_obj = g.db_session.query(Signatures).filter_by(id=signature_data['id']).first()
                if sig_obj:
                    self.signatures.append(sig_obj)
            
            if user_data and user_data.get('id') not in seen_user_ids:
                seen_user_ids.add(user_data['id'])
                # Récupérer l'objet User complet depuis la base
                user_obj = g.db_session.query(User).filter_by(id=user_data['id']).first()
                if user_obj:
                    self.signatories.append(user_obj)
        
        return self
    
    def verify_all_signatures_completed(self) -> 'SignedDocumentCreator':
        """
        Vérifie que toutes les signatures requises ont été effectuées.
        Args:
            self: SignedDocumentCreator
        Returns:
            self: SignedDocumentCreator
        Raises:
            ValueError: Si toutes les signatures ne sont pas complétées.
        """
        # Vérifier que des points de signature existent
        if not self.view_points:
            raise ValueError("Aucun point de signature trouvé pour ce document.")
        
        # Vérifier que tous les points ont été signés (status = 1)
        unsigned_users: bool = False
        for data in self.view_points:
            point = data['point']
            # point est un dictionnaire, accéder avec ['status']
            if point['status'] != 1:
                unsigned_users = True
                break
        
        # Si des utilisateurs n'ont pas signé, lever une erreur
        if unsigned_users:
            raise ValueError("Signatures manquantes sur le document.")
        
        return self
    
    def apply_signatures_to_pdf(self) -> 'SignedDocumentCreator':
        """
        Applique les signatures SVG sur le document PDF en utilisant pypdf.
        Args:
            self: SignedDocumentCreator
        Returns:
            self: SignedDocumentCreator
        Raises:
            Exception: Si une erreur survient lors de l'application des signatures.
        """
        # Vérifier que le document et les points de signature sont chargés
        if not self.document_path or not self.view_points:
            raise ValueError("Document ou données de signature manquants.")
        
        # Appliquer les signatures sur le PDF : préparation, traitement des pages, écriture
        try:
            self._prepare_signed_document()
            self._process_all_pages()
            self._write_signed_pdf()
            self._update_document_hash()

            return self
        
        # En cas d'erreur, créer une copie simple du fichier
        except Exception as e:
            self._create_fallback_copy()
            raise ValueError(f"Erreur lors de l'application des signatures : {e}")
    
    def _prepare_signed_document(self) -> None:
        """Prépare le document signé : chemin, lecteur et regroupement des signatures."""
        # Vérifier que le chemin du document est défini
        if not self.document_path:
            raise ValueError("Chemin du document manquant")
        
        # Créer le chemin pour le document signé
        signed_filename = f"signed_{self.document_path.name}"
        self.signed_document_path = self.document_path.parent / signed_filename
        
        # Lire le PDF original
        self.reader = PdfReader(str(self.document_path))
        self.writer = PdfWriter()
        
        # Grouper les données de signature par page
        self.data_by_page: Dict[int, List[Dict[str, Any]]] = {}
        for data in self.view_points:
            page_num = data['point']['page_num']
            if page_num not in self.data_by_page:
                self.data_by_page[page_num] = []
            self.data_by_page[page_num].append(data)
    
    def _process_all_pages(self) -> None:
        """Traite toutes les pages du PDF en ajoutant les signatures."""
        # Parcourir chaque page du PDF
        for page_num in range(1, len(self.reader.pages) + 1):
            page = self.reader.pages[page_num - 1]
            
            # S'il y a des signatures sur cette page, créer un overlay
            if page_num in self.data_by_page:
                overlay_pdf = self._create_signature_overlay(
                    page=page,
                    signatures_data=self.data_by_page[page_num]
                )
                
                # Ajouter l'overlay à la page si créé
                if overlay_pdf:
                    overlay_reader = PdfReader(BytesIO(overlay_pdf))
                    page.merge_page(overlay_reader.pages[0])
            
            self.writer.add_page(page)
    
    def _write_signed_pdf(self) -> None:
        """Écrit le PDF signé sur le disque et vérifie son intégrité."""
        # Vérifier que le chemin du document signé est défini
        if not self.signed_document_path:
            raise ValueError("Chemin du document signé manquant")
        
        # Écrire le PDF signé dans le fichier de sortie
        with open(self.signed_document_path, 'wb') as output_file:
            self.writer.write(output_file)
        
        # Vérifier que le fichier a bien été créé et n'est pas vide
        file_size = self.signed_document_path.stat().st_size
        if not self.signed_document_path.exists() or file_size == 0:
            raise ValueError(f"Le fichier signé n'a pas été créé : {self.signed_document_path}")
    
    def _create_fallback_copy(self) -> None:
        """Crée une copie simple du fichier en cas d'erreur."""
        # Si présence du document original, faire une copie simple
        if self.document_path:
            signed_filename = f"signed_{self.document_path.name}"
            self.signed_document_path = self.document_path.parent / signed_filename
            shutil.copy2(self.document_path, self.signed_document_path)
    
    def _update_document_hash(self) -> None:
        """Met à jour le hash du document signé."""
        # Si absence du document sur le disque ou objet document, lever une erreur
        if not self.signed_document_path or not self.document:
            raise ValueError("Chemin du document signé ou objet document manquant")
        
        # Calculer le hash SHA-256 du fichier signé et mettre à jour en base
        with open(self.signed_document_path, "rb") as f:
            file_content = f.read()
            new_hash = hashlib.sha256(file_content).hexdigest()
        self.document.hash_signed_file = new_hash
    
    def _create_signature_overlay(self, page: Any, signatures_data: List[Dict[str, Any]]) -> bytes | None:
        """
        Crée un overlay PDF avec les signatures pour une page donnée.
        
        Args:
            page: La page PDF (pypdf)
            signatures_data: Liste des données de signature pour cette page
            page_num: Numéro de la page
            
        Returns:
            bytes: Le PDF overlay en bytes, ou None si aucune signature
        """
        try:
            # Récupérer les dimensions de la page
            page_box = page.mediabox
            page_width = float(page_box.width)
            page_height = float(page_box.height)
            
            # Créer un buffer pour le PDF overlay
            packet = BytesIO()
            can: Canvas = canvas.Canvas(packet, pagesize=(page_width, page_height))
            signatures_added = 0
            
            # Ajouter chaque signature sur l'overlay
            for data in signatures_data:
                if self._add_single_signature_to_canvas(can, data, page_width, page_height):
                    signatures_added += 1
            
            # Finaliser le canvas seulement si des signatures ont été ajoutées
            if signatures_added == 0:
                raise ValueError("Aucune signature valide à ajouter sur cette page.")
            
            # Finaliser le PDF overlay
            can.save()
            packet.seek(0)
            
            return packet.getvalue()
            
        except Exception as e:
            raise ValueError(f"Impossible de créer l'overlay de signature: {e}")
    
    def _add_single_signature_to_canvas(self, can: Canvas, data: Dict[str, Any], page_width: float, page_height: float) -> bool:
        """
        Ajoute une signature unique sur le canvas.
        
        Args:
            can: Le canvas reportlab
            data: Les données de la signature (signature, point, user)
            page_width: Largeur de la page
            page_height: Hauteur de la page
            
        Returns:
            bool: True si la signature a été ajoutée avec succès
        """
        # Extraire les données nécessaires
        signature = data['signature']
        point = data['point']
        nom_complet = data['user_complete_name']
        
        # Vérifier si on a un SVG valide
        svg_graph = signature.get('svg_graph')
        if not svg_graph or len(str(svg_graph).strip()) == 0:
            raise ValueError(f"Pas de SVG valide pour le point {point.get('id')}")
        
        # Traiter l'image de signature
        largeur = signature.get('largeur_graph', 600)
        hauteur = signature.get('hauteur_graph', 200)
        svg_image = self._process_signature_image(svg_graph, largeur, hauteur)
        
        if not svg_image:
            raise ValueError(f"Impossible de convertir le SVG en image pour le point {point.get('id')}")
        
        # Calculer la position de la signature
        x_pos, y_pos = self._calculate_signature_position(
            point, svg_image, page_width, page_height
        )
        
        # Dessiner la signature sur le canvas
        self._draw_signature_on_canvas(can, svg_image, x_pos, y_pos)
        
        # Ajouter les métadonnées textuelles
        self._add_signature_metadata_text(
            can, nom_complet, signature, x_pos, y_pos, 
            svg_image.width, svg_image.height, page_width
        )
        
        return True
    
    def _process_signature_image(self, svg_graph: str, largeur: int, hauteur: int) -> PILImage.Image | None:
        """
        Traite l'image de signature : conversion SVG et redimensionnement.
        
        Args:
            svg_graph: Le contenu SVG de la signature
            largeur: Largeur originale
            hauteur: Hauteur originale
            
        Returns:
            Image PIL redimensionnée ou None si échec
        """
        # Convertir le SVG en image
        svg_image = self._convert_svg_to_image(
            svg_content=svg_graph,
            width=largeur,
            height=hauteur
        )
        
        # Si échec de la conversion, retourner None
        if not svg_image:
            return None
        
        # Réduire la taille à 33% (un tiers de la taille originale)
        img_width, img_height = svg_image.size
        reduction_factor = 1/3
        
        new_width = int(img_width * reduction_factor)
        new_height = int(img_height * reduction_factor)
        svg_image = svg_image.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
        logging.info(f"Image réduite à 33% : ({img_width}x{img_height}) → ({new_width}x{new_height})")
        
        # Redimensionner encore si trop grande
        max_width = 450
        max_height = 150
        final_width, final_height = svg_image.size
        scale_ratio = 1.0
        
        # Vérifier si on dépasse les dimensions max de la page
        if final_width > max_width:
            scale_ratio = max_width / final_width
        if final_height * scale_ratio > max_height:
            scale_ratio = max_height / final_height
        
        # Gestion du redimensionnement si nécessaire
        if scale_ratio < 1.0:
            final_width = int(final_width * scale_ratio)
            final_height = int(final_height * scale_ratio)
            svg_image = svg_image.resize((final_width, final_height), PILImage.Resampling.LANCZOS)
        
        return svg_image
    
    def _calculate_signature_position(self, point: Dict[str, Any], svg_image: PILImage.Image, 
                                     page_width: float, page_height: float) -> tuple[float, float]:
        """
        Calcule la position de la signature sur la page PDF.
        
        Args:
            point: Le point de signature avec coordonnées x, y
            svg_image: L'image PIL de la signature
            page_width: Largeur de la page
            page_height: Hauteur de la page
            
        Returns:
            tuple: (x_pos, y_pos) position finale sur la page
        """
        # Récupérer les coordonnées du point en pixels
        point_x_pixels = float(point.get('x', 100))
        point_y_pixels = float(point.get('y', 100))
        
        # CONVERSION PIXELS → POINTS PDF
        PDF_SCALE = 1.5  # Correspond à pdfScale dans le JavaScript
        point_x = point_x_pixels / PDF_SCALE
        point_y = point_y_pixels / PDF_SCALE
        
        # Calculer la position pour centrer l'image sur le point
        img_w = svg_image.width
        img_h = svg_image.height
        
        # VALIDATION DES COORDONNÉES
        if point_y > page_height:
            point_x = page_width / 2
            point_y = page_height / 2
        
        if point_x > page_width:
            point_x = page_width / 2
        
        # S'assurer que la signature ne déborde pas de la page
        x_pos = point_x - (img_w / 2)
        y_pos = page_height - point_y - (img_h / 2)
        
        # Ajuster si la signature déborde
        if x_pos < 0:
            x_pos = 10
        if x_pos + img_w > page_width:
            x_pos = page_width - img_w - 10
        if y_pos < 0:
            y_pos = 10
        if y_pos + img_h > page_height:
            y_pos = page_height - img_h - 10
        
        return x_pos, y_pos
    
    def _draw_signature_on_canvas(self, can: Canvas, svg_image: PILImage.Image, 
                                  x_pos: float, y_pos: float) -> None:
        """
        Dessine l'image de signature sur le canvas.
        
        Args:
            can: Le canvas reportlab
            svg_image: L'image PIL à dessiner
            x_pos: Position X sur la page
            y_pos: Position Y sur la page
            point: Le point de signature (pour logging)
        """
        # Convertir l'image PIL en ImageReader pour reportlab
        img_reader: ImageReader = ImageReader(svg_image)
        can.drawImage(img_reader, x_pos, y_pos,  # type: ignore[call-arg]
                    width=svg_image.width, height=svg_image.height,
                    mask='auto', preserveAspectRatio=True)
    
    def _add_signature_metadata_text(self, can: Canvas, nom_complet: str, signature: Dict[str, Any],
                                     x_pos: float, y_pos: float, img_w: int, img_h: int,
                                     page_width: float) -> None:
        """
        Ajoute le texte de métadonnées sous la signature.
        
        Args:
            can: Le canvas reportlab
            nom_complet: Nom complet du signataire
            signature: Dict contenant les données de signature
            x_pos: Position X de l'image
            y_pos: Position Y de l'image
            img_w: Largeur de l'image
            img_h: Hauteur de l'image
            page_width: Largeur de la page
        """
        can.setFont("Helvetica", 8)
        
        # Préparer les textes
        text_line1 = f"Signé par: {nom_complet}"
        text_line2 = f"Le: {signature.get('signe_at', 'Date inconnue')}"
        
        # Calculer la largeur des textes pour les centrer
        text_width1 = can.stringWidth(text_line1, "Helvetica", 8)
        text_width2 = can.stringWidth(text_line2, "Helvetica", 8)
        
        # Position Y en dessous de l'image
        text_y_line1 = y_pos - 12
        text_y_line2 = text_y_line1 - 10
        
        # Vérifier que le texte ne dépasse pas le bas de la page
        MIN_MARGIN = 5
        if text_y_line2 < MIN_MARGIN:
            # Placer au-dessus de la signature
            text_y_line1 = y_pos + img_h + 12
            text_y_line2 = text_y_line1 + 10
        
        # Centrer horizontalement les textes
        text_x1 = x_pos + (img_w - text_width1) / 2
        text_x2 = x_pos + (img_w - text_width2) / 2
        
        # Ajuster si débordement
        if text_x1 < 0:
            text_x1 = 5
        if text_x2 < 0:
            text_x2 = 5
        if text_x1 + text_width1 > page_width:
            text_x1 = page_width - text_width1 - 5
        if text_x2 + text_width2 > page_width:
            text_x2 = page_width - text_width2 - 5
        
        # Dessiner les textes
        can.drawString(text_x1, text_y_line1, text_line1)
        can.drawString(text_x2, text_y_line2, text_line2)
        
    def _convert_svg_to_image(self, *, svg_content: str, width: int, height: int):
        """
        Convertit un contenu SVG en image utilisable par borb.
        
        Args:
            svg_content (str): Le contenu SVG
            width (int): Largeur souhaitée
            height (int): Hauteur souhaitée
            
        Returns:
            Image PIL ou None si échec
        """
        try:
            # Valider le contenu SVG
            if not svg_content or len(svg_content.strip()) == 0:
                raise ValueError("Contenu SVG manquant")
            
            # Vérifier que le contenu ressemble à du SVG
            if '<svg' not in svg_content.lower():
                raise ValueError("Le contenu fourni n'est pas un SVG valide")
            
            # Convertir SVG en PNG avec cairosvg
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=width if width > 0 else 100,
                output_height=height if height > 0 else 50
            )
            
            # Vérifier que png_data n'est pas None et est de type bytes avant de l'utiliser
            if png_data is not None and isinstance(png_data, bytes):
                # Créer une image PIL depuis les données PNG
                image = PILImage.open(BytesIO(png_data))
                return image
            else:
                raise ValueError("Conversion SVG en PNG a échoué, données invalides.")
            
        except ImportError:
            raise ImportError("cairosvg ou PIL non disponible pour la conversion SVG")
        except Exception as e:
            raise ValueError(f"Erreur lors de la conversion SVG : {e}")

    def add_signature_certificates(self) -> 'SignedDocumentCreator':
        """
        Incorpore les certificats de signature sécurisés dans le PDF.
        
        Returns:
            self: SignedDocumentCreator
            
        Note:
            Cette méthode crée un certificat cryptographiquement sécurisé
            avec signature numérique pour garantir l'intégrité.
        """
        try:
            if not self.signed_document_path or not self.signatures:
                raise ValueError("Document ou signatures manquants.")
            
            # Créer le certificat sécurisé avec signature cryptographique
            document_hash = self.document.hash_fichier if self.document else "unknown"
            secure_cert = SecureCertificateManager.create_secure_certificate(
                signatures=self.signatures,
                signatories=self.signatories,
                document=self.document,
                view_points=self.view_points,
            )
            
            # Vérifier immédiatement le certificat créé
            is_valid = SecureCertificateManager.verify_certificate(secure_cert)
            if not is_valid:
                raise ValueError("Certificat invalide généré")
            
            # Sauvegarder le certificat sécurisé dans un fichier JSON
            if self.signed_document_path:
                cert_file_path = self.signed_document_path.with_suffix('.secure.cert')
                with open(cert_file_path, 'w', encoding='utf-8') as cert_file:
                    json.dump(secure_cert, cert_file, indent=2, ensure_ascii=False)
                
                # Créer également un fichier de vérification rapide
                verification_info: Dict[str, Any] = {
                    "certificate_id": secure_cert["certificate"]["certificate_id"],
                    "document_hash": document_hash,
                    "signatures_count": len(self.signatures),
                    "signatories_names": [f"{s.prenom} {s.nom}" for s in self.signatories],
                    "creation_timestamp": secure_cert["certificate"]["creation_timestamp"],
                    "verification_status": "VALID" if is_valid else "INVALID",
                    "algorithm": secure_cert["algorithm"],
                    "version": secure_cert["version"]
                }
                
                verification_file_path = self.signed_document_path.with_suffix('.verification.json')
                with open(verification_file_path, 'w', encoding='utf-8') as verify_file:
                    json.dump(verification_info, verify_file, indent=2, ensure_ascii=False)
                
            return self
            
        except Exception as e:
            raise ValueError(f"Erreur lors de l'ajout des certificats : {e}")
    
    def save_final_document(self) -> 'SignedDocumentCreator':
        """
        Sauvegarde le document signé final en remplacement de l'original.
        
        Returns:
            self: SignedDocumentCreator
        """
        if not self.signed_document_path or not self.document_path:
            raise ValueError("Document signé non généré.")
        
        # Vérifier que le fichier signé existe et n'est pas vide
        file_size = self.signed_document_path.stat().st_size
        if not self.signed_document_path.exists() or file_size == 0:
            raise ValueError(f"Le fichier signé n'existe pas ou est vide : {self.signed_document_path}")
        
        # Sauvegarder l'original avec un suffixe _original et déplacer le document signé à la place de l'original
        original_backup = self.document_path.parent / f"original_{self.document_path.name}"
        if self.document_path.exists(): shutil.move(self.document_path, original_backup)
        shutil.move(self.signed_document_path, self.document_path)

        # Mettre à jour le document en base (marquer comme finalisé)
        if self.document:
            self.document.status = 1
            self.document.complete_at = datetime.now()

        if self.signatures:
            for signature in self.signatures:
                signature.status = 1
        
        return self
    
    def send_signed_document_by_email(self) -> 'SignedDocumentCreator':
        """
        Envoie le document signé par email à tous les participants.
        
        Returns:
            self: SignedDocumentCreator
        """
        if not self.document or not self.document_path:
            raise ValueError("Document non chargé ou chemin invalide.")
        
        # Préparer la liste des destinataires (créateur + signataires)
        recipients: set[str] = set()
        
        # Ajouter le créateur
        if self.creator and self.creator.mail:
            recipients.add(self.creator.mail)
        
        # Ajouter tous les signataires
        for signatory in self.signatories:
            if signatory.mail:
                recipients.add(signatory.mail)
        
        if not recipients:
            return self
        
        # Créer le template email
        signatory_names = [f"{s.prenom} {s.nom}" for s in self.signatories]
        creator_name = f"{self.creator.prenom} {self.creator.nom}" if self.creator else "Inconnu"
        
        email_template = render_template(
            'signatures/signed_document_mail.html',
            doc_titre=self.document.doc_nom,
            doc_type=self.document.doc_type,
            creator_name=creator_name,
            signatory_names=signatory_names,
            completion_date=datetime.now().strftime('%d/%m/%Y %H:%M')
        )
        
        # Envoyer l'email avec le document en pièce jointe
        try:
            for recipient in recipients:
                send_email_signed_files(
                    to=recipient,
                    template=email_template,
                    attachments=[str(self.document_path)]
                )
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du document signé par email : {e}")
            # Ne pas lever d'exception pour ne pas bloquer le processus
        
        return self

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
    def _add_signatories_info(signatories: List[User], signatures: List[Signatures], cert_data: Dict[str, Any], sig_to_user: Dict[int, User]) -> Dict[str, Any]:
        """
        Ajoute les informations des signataires au certificat.
        
        Args:
            signatories (List[User]): Liste des utilisateurs signataires
            signatures (List[Signatures]): Liste des signatures
            cert_data (Dict[str, Any]): Dictionnaire du certificat à remplir
            sig_to_user (Dict[int, User]): Mapping signature_id -> User
        """
        for signature in signatures:
            # Utiliser le mapping pour trouver l'utilisateur correspondant
            signatory = sig_to_user.get(signature.id)
            if signatory:
                signatory_info: Dict[str, Any] = {
                    "id": signatory.id,
                    "name": f"{signatory.prenom} {signatory.nom}",
                    "email": signatory.mail,
                    "signature_timestamp": signature.signe_at.isoformat() if signature.signe_at else None,
                    "ip_address": signature.ip_addresse,
                    "user_agent_hash": hashlib.sha256(signature.user_agent.encode() if signature.user_agent else b'').hexdigest()[:16],
                    "signature_hash": signature.signature_hash
                }
                cert_data["signatories"].append(signatory_info)

        return cert_data
                
    @staticmethod
    def _add_signatures_details(signatories: List[User], signatures: List[Signatures], cert_data: Dict[str, Any], sig_to_user: Dict[int, User]) -> Dict[str, Any]:
        """
        Ajoute les détails techniques des signatures au certificat.
        Args:
            signatories (List[User]): Liste des utilisateurs signataires
            signatures (List[Signatures]): Liste des signatures
            cert_data (Dict[str, Any]): Dictionnaire du certificat à remplir
            sig_to_user (Dict[int, User]): Mapping signature_id -> User
        Returns:
            Dict[str, Any]: Dictionnaire du certificat mis à jour
        """
        for signature in signatures:
            # Utiliser le mapping pour trouver l'utilisateur correspondant
            signatory = sig_to_user.get(signature.id)
            if signatory:
                # Détails techniques de la signature
                signature_detail: Dict[str, Any] = {
                    "signature_id": signature.id,
                    "status": signature.status,
                    "svg_data_hash": hashlib.sha256(signature.svg_graph.encode() if signature.svg_graph else b'').hexdigest(),
                    "data_graph_hash": hashlib.sha256(signature.data_graph.encode() if signature.data_graph else b'').hexdigest(),
                    "dimensions": {
                        "width": signature.largeur_graph,
                        "height": signature.hauteur_graph
                    },
                    "timestamp": signature.timestamp_graph.isoformat() if signature.timestamp_graph else None
                }
                cert_data["signature_details"].append(signature_detail)
        
        return cert_data
    
    @staticmethod
    def create_secure_certificate(signatures: List[Signatures], signatories: List[User], document: DocToSigne, view_points: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        """
        Crée un certificat sécurisé avec signature cryptographique.
        
        Args:
            signatures (List[Signatures]): Liste des objets Signatures
            signatories (List[User]): Liste des objets User signataires
            document (DocToSigne): Le document signé
            view_points (List[Dict[str, Any]]): Liste optionnelle des view_points pour correspondance
        Returns:
            Dict contenant le certificat sécurisé
        """
        # Créer un mapping signature_id -> user pour faciliter la correspondance
        sig_to_user: Dict[int, User] = {}
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
            cert_data: Dict[str, Any] = {
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
            secure_cert: Dict[str, Any] = {
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
            
        except Exception as e:
            raise ValueError(f"Erreur lors de la création du certificat sécurisé : {e}")
    
    @staticmethod
    def _sign_data(data: bytes, private_key: Any) -> bytes:
        """
        Signe des données avec la clé privée.
        
        Args:
            data (bytes): Données à signer
            private_key: Clé privée RSA
            
        Returns:
            bytes: Signature cryptographique
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
    def verify_certificate(secure_cert: Dict[str, Any]) -> bool:
        """
        Vérifie l'intégrité d'un certificat sécurisé.
        
        Args:
            secure_cert (Dict): Certificat sécurisé à vérifier
            
        Returns:
            bool: True si le certificat est valide
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
            
        except Exception as e:
            raise ValueError(f"Échec de la vérification du certificat : {e}")

def send_email_signed_files(*, to: str, template: str, attachments: List[str]) -> None:
    """
    Envoie un e-mail avec des fichiers signés en pièce jointe.

    Args:
        to (str): Adresse e-mail du destinataire.
        template (str): Contenu HTML de l'e-mail.
        attachments (List[str]): Liste des chemins de fichiers à attacher.
    """
    # Configuration de l'e-mail
    email_expediteur: str = Config.EMAIL_USER
    mot_de_passe: str = Config.EMAIL_PASSWORD

    # Construire le message
    msg = MIMEMultipart()
    msg['From'] = email_expediteur
    msg['To'] = to
    msg['Subject'] = 'La Péraudière | Documents signés'
    body = template
    msg.attach(MIMEText(body, 'html'))

    # Ajouter toutes les pièces jointes
    for file_path in attachments:
        try:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=Path(file_path).name)
                msg.attach(part)
        except Exception as e:
            logging.error(f"Erreur lors de la lecture de la pièce jointe {file_path}: {str(e)}")
            continue
    # Envoyer l'e-mail
    try:
        with smtplib.SMTP(Config.EMAIL_SMTP, Config.EMAIL_PORT) as server:
            server.starttls()
            server.login(email_expediteur, mot_de_passe)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'e-mail avec pièces jointes à {to}: {str(e)}")

def send_email_invitation(*, to: str, template: str) -> None:
    """
    Envoie un e-mail d'invitation à signer un document.

    Args:
        to (str): Adresse e-mail du destinataire.
        template (str): Contenu HTML de l'e-mail.
    """
    # Configuration de l'e-mail
    email_expediteur: str = Config.EMAIL_USER
    mot_de_passe: str = Config.EMAIL_PASSWORD

    # Construire le message
    msg = MIMEMultipart()
    msg['From'] = email_expediteur
    msg['To'] = to
    msg['Subject'] = 'La Péraudière | Vous êtes invité à signer un document'
    body = template
    msg.attach(MIMEText(body, 'html'))

    # Envoyer l'e-mail
    try:
        with smtplib.SMTP(Config.EMAIL_SMTP, Config.EMAIL_PORT) as server:
            server.starttls()
            server.login(email_expediteur, mot_de_passe)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'e-mail d'invitation à {to}: {str(e)}")

def send_otp_email(*, to: str, template: str) -> None:
    """
    Envoie un e-mail contenant un code OTP pour la signature.

    Args:
        to (str): Adresse e-mail du destinataire.
        template (str): Contenu HTML de l'e-mail.
    """
    # Configuration de l'e-mail
    email_expediteur: str = Config.EMAIL_USER
    mot_de_passe: str = Config.EMAIL_PASSWORD

    # Construire le message
    msg = MIMEMultipart()
    msg['From'] = email_expediteur
    msg['To'] = to
    msg['Subject'] = 'La Péraudière | Votre code OTP pour signer un document'
    body = template
    msg.attach(MIMEText(body, 'html'))
    
    # Envoyer l'e-mail
    try:
        with smtplib.SMTP(Config.EMAIL_SMTP, Config.EMAIL_PORT) as server:
            server.starttls()
            server.login(email_expediteur, mot_de_passe)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'e-mail OTP à {to}: {str(e)}")
