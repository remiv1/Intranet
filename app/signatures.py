"""
Page des gestion des fonctions liées à la signature électronique.
Fonctions:
- Ajout de la signature graphique sur un document PDF.
- Ajout d'un certificat de signature numérique.
- Stockage temporaire des documents avant signature.
- Enregistrement des ashages des documents signés pour vérification ultérieure.
"""
import hmac
import json
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from os import getenv
from flask import render_template, request, Request, g, session
from models import DocToSigne, Invitation, Points, Signatures, User
import logging, smtplib
from config import Config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BAD_INVITATION = 'Invitation invalide ou non trouvée.'

class SignatureDoer:
    """
    Gère le processus de signature d'un document.
    Attributes:
        request (Request): L'objet request Flask.
        signatory_id (int | None): L'ID de l'utilisateur signataire.
        signatory_name (str | None): Le nom complet de l'utilisateur signataire.
        document (DocToSigne | None): Le document à signer.
        invitation (Invitation | None): L'invitation associée au document et à l'utilisateur
        token (str | None): Le token d'invitation.
        otp (str | None): Le code OTP soumis par l'utilisateur.
        ip_addresse (str | None): L'adresse IP de l'utilisateur.
        user_agent (str | None): Le User-Agent de l'utilisateur.
        signature_hash (str | None): Le hash de la signature.
        svg_graph (str | None): Le graphique SVG de la signature.
        data_graph (str | None): Les données de la signature.
        largeur_graph (int): La largeur du graphique de la signature.
        hauteur_graph (int): La hauteur du graphique de la signature.
        datetime_submission (datetime | None): La date et l'heure de la soumission de la signature.
        object_points (List[Points] | None): Liste des objets Points associés à la signature.
        points (List[Dict[str, Any]] | None): Liste des points de signature sérialisés.
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
        Attributes:
            request (Request): L'objet request Flask.
            signatory_id (int | None): L'ID de l'utilisateur signataire.
            signatory_name (str | None): Le nom complet de l'utilisateur signataire.
            document (DocToSigne | None): Le document à signer.
            invitation (Invitation | None): L'invitation associée au document et à l'utilisateur.
        Exemples:
            ```python
            doer = SignatureDoer(request)
            ```
        """
        self.request = request

    def get_request(self, *, id_document: int, hash_document: str) -> 'SignatureDoer':
        """
        Récupère les données de la requête.
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
        self.signatory_name = f"{session.get('prenom', '')} {session.get('nom', '')}".strip()

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
        Traite la soumission du formulaire de signature.
        Returns:
            self: SignatureDoer
        Raises:
            ValueError: Si le document ou l'invitation n'est pas trouvé ou invalide
        Exemples:
            ```python
            doer = SignatureDoer(request).get_request().post_request()
            ```
        """
        self.token = self.request.headers.get('X-Invit-Token', None)
        self.ip_addresse = self.request.environ.get('REMOTE_ADDR') or self.request.remote_addr
        data = self.request.get_json()
        if not data:
            raise ValueError("Données de signatures invalides ou manquantes.")        
        self.otp = data.get('otp_code', None)
        
        # Nouvelles données haute précision
        self.signature_hash = data.get('signature_hash', None)
        self.user_agent = data.get('user_agent', None)
        self.svg_graph = data.get('svg_graph', None)
        self.data_graph = data.get('data_graph', None)
        self.largeur_graph = data.get('largeur_graph', 0)
        self.hauteur_graph = data.get('hauteur_graph', 0)
        
        self.datetime_submission = datetime.now()
        self.signatory_id = session.get('id', None)
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
        Returns:
            self: SignatureDoer
        Exemples:
            ```python
            doer = SignatureDoer(request).get_request().get_signature_points()
            ```
        """
        self.object_points = g.db_session.query(Points) \
                        .filter_by(id_document=self.document.id, id_user=self.signatory_id) \
                        .all()
        self.points: List[Dict[str, Any]] = [point.to_dict() for point in self.object_points]
        
        return self
    
    def handle_signature_submission(self) -> 'SignatureDoer':
        """
        Gère la soumission de la signature.
        Returns:
            self: SignatureDoer
        """
        otp_valid = (self.otp == self.invitation.code_otp)  # Remplacer par la validation réelle de l'OTP si nécessaire
        if self.document.status == 1:
            raise ValueError("Le document a déjà été signé.")
        elif self.invitation.expire_at < datetime.now():
            raise ValueError("L'invitation a expiré.")
        elif not self.document or not self.invitation or not self.points or not otp_valid:
            raise ValueError(BAD_INVITATION)
        
        # Mise à jour du document
        self.document.status = 1  # Statut signé
        self.document.complete_at = self.datetime_submission

        # Création de l'entrée dans la table Signatures
        signature: Signatures = Signatures(
            signe_at=self.datetime_submission,
            signature_hash=self.signature_hash or 'unknown',
            ip_addresse=self.ip_addresse,
            user_agent=self.user_agent or self.request.headers.get('User-Agent', 'unknown'),
            statut=1,  # Statut signé
            svg_graph=self.svg_graph,
            data_graph=self.data_graph,
            largeur_graph=self.largeur_graph,
            hauteur_graph=self.hauteur_graph,
            timestamp_graph=self.datetime_submission,
        )
        g.db_session.add(signature)
        g.db_session.flush()

        # Mise à jour des points de signature
        for point in self.object_points:
            point.status = 1  # Statut signé
            point.signe_at = self.datetime_submission
            point.id_signature = signature.id

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
    Methods:
        get_request():
            Récupère les données du formulaire de la requête.
        get_signature_points():
            Récupère les points de signature du formulaire de la requête.
        fix_documents():
            Renomme le document dans le dossier temporaire vers le dossier final.
    """
    def __init__(self, request: Request):
        """
        Initialise avec l'objet request Flask.
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
        Exemples:
            ```python
            maker = SignatureMaker(request)
            ```
        """
        self.request = request

    def get_request(self) -> 'SignatureMaker':
        """
        Récupère les données du formulaire de la requête.
        Returns:
            self: SignatureMaker
        """
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
        Returns:
            self: SignatureMaker
        """
        self.points: list[Dict[str, Any]] = []
        i = 0
        while f'signature_points[{i}][x]' in self.request.form:
            point: Dict[str, float | int] = {
                'x': float(self.request.form.get(f'signature_points[{i}][x]', 0)),
                'y': float(self.request.form.get(f'signature_points[{i}][y]', 0)),
                'page_num': int(self.request.form.get(f'signature_points[{i}][pageNum]', 1)),
                'user_id': int(self.request.form.get(f'signature_points[{i}][user_id]', 1)),
            }
            self.points.append(point)
            i += 1
        return self
    
    def create_document(self) -> 'SignatureMaker':
        """
        Crée un document à signer.
        Returns:
            self: SignatureMaker
        """
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
        g.db_session.add(self.doc_to_signe)
        g.db_session.flush()
        return self
    
    def create_points(self) -> 'SignatureMaker':
        """
        Crée les points de signature dans la base de données.
        Returns:
            self: SignatureMaker
        """
        for point in self.points:
            signature_point: Points = Points(
                id_document=self.doc_to_signe.id,
                id_user=point['user_id'],
                page_num=point['page_num'],
                x=point['x'],
                y=point['y']
            )
            g.db_session.add(signature_point)
        return self
    
    def fix_documents(self) -> 'SignatureMaker':
        """
        Renomme le document dans le dossier temporaire vers le dossier final.
        Returns:
            self: SignatureMaker
        Raises:
            FileNotFoundError: Si le fichier source n'existe pas.
            IOError: Si une erreur survient lors du renommage du fichier.
        """
        if self.old_name and self.new_name:
            temp_dir = SecureDocumentAccess.TEMP_DIR
            final_dir = getenv('SIGNATURE_DOCKER_PATH', '/tmp/')
            Path(final_dir).mkdir(parents=True, exist_ok=True)
            old_path = Path(temp_dir) / self.old_name
            new_path = Path(final_dir) / self.new_name
            if old_path.exists():
                try:
                    file_path = shutil.move(str(old_path), str(new_path))
                    with open(new_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        self.doc_to_signe.chemin_fichier = file_path
                        self.doc_to_signe.hash_fichier = file_hash
                    return self
                except Exception:
                    raise IOError("Erreur lors du renommage du fichier.")
            else:
                raise FileNotFoundError("Le fichier source n'existe pas.")
        raise FileNotFoundError("Le fichier source n'existe pas ou les noms sont invalides.")
    
    def send_invitation(self) -> 'SignatureMaker':
        """
        Envoie une invitation aux utilisateurs pour signer le document.
        Returns:
            self: SignatureMaker
        """
        # Récupération de la liste des mails, noms et prénoms des utilisateurs
        user_ids = {point['user_id'] for point in self.points}
        users = g.db_session.query(User).filter(User.id.in_(user_ids)).all()
        self.token = hmac.new(
            getenv('SECRET_KEY', 'default-secret-key').encode(),
            f"{self.doc_to_signe.id}-{self.doc_to_signe.hash_fichier}-{datetime.now().isoformat()}".encode(),
            hashlib.sha256
        ).hexdigest()
        self.limite_signature = datetime.now() + timedelta(days=int(self.doc_to_signe.echeance) if self.doc_to_signe.echeance and str(self.doc_to_signe.echeance).isdigit() else 3)
        for user in users:
            # Création d'une invitation dans la table Invitation
            invitation: Invitation = Invitation(
                id_document=self.doc_to_signe.id,
                id_user=user.id,
                token=self.token,
                expire_at=self.limite_signature,
                mail_envoye=True,
                mail_compte=1
            )
            g.db_session.add(invitation)
            g.db_session.flush()
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
        get_user_identifier() -> str:
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
    TEMP_DIR = getenv('TEMP_DOCKER_PATH', '/tmp') + '/signature'  # Constante pour le dossier temporaire
    
    @staticmethod
    def get_user_identifier() -> str:
        """
        Génère un identifiant unique pour l'utilisateur basé sur session, IP et User-Agent.
        """
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
        """
        if not user_identifier:
            user_identifier = SecureDocumentAccess.get_user_identifier()
        
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
        """
        temp_dir = Path(SecureDocumentAccess.TEMP_DIR)
        temp_dir.mkdir(exist_ok=True)
        
        access_data: Dict[str, Any] = {
            "filename": filename,
            "hash": document_hash,
            "user_identifier": SecureDocumentAccess.get_user_identifier(),
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now().timestamp() + 86400)  # 24h en secondes
        }
        
        # Nom du fichier JSON basé sur le hash
        json_file = temp_dir / f"{document_hash}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(access_data, f, indent=2)
    
    @staticmethod
    def verify_temp_access(filename: str) -> bool:
        """
        Vérifie l'accès au document via les fichiers temporaires.
        Args:
            filename (str): Le nom du fichier à vérifier.
        Returns:
            bool: True si l'accès est valide, False sinon.
        """
        user_identifier = SecureDocumentAccess.get_user_identifier()
        temp_dir = Path(SecureDocumentAccess.TEMP_DIR)
        
        if not temp_dir.exists():
            return False
        
        # Chercher tous les fichiers JSON dans temp/
        json_files = list(temp_dir.glob("*.json"))
        
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
        """
        temp_dir = Path(SecureDocumentAccess.TEMP_DIR)
        if not temp_dir.exists():
            return
            
        current_time = datetime.now().timestamp()
        
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

def send_email_invitation(*, to: str, template: str) -> None:
    # Configuration de l'e-mail
    email_expediteur: str = Config.EMAIL_USER
    mot_de_passe: str = Config.EMAIL_PASSWORD

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
    # Configuration de l'e-mail
    email_expediteur: str = Config.EMAIL_USER
    mot_de_passe: str = Config.EMAIL_PASSWORD

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
