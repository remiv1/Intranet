"""
Blueprint pour la gestion de services de signature électronique.

Routes:
- /signature/deposer : Permet de déposer un document à signer.
- /signature/signer/<doc_id>/<hash_document> : Permet de signer un document.
- /signature/liste : Affiche la liste des documents à signer.
- /signature/creer-depuis-modele : Permet de créer un document à signer depuis un modèle.
- /signature/charger-pdf : Permet de charger un document PDF à signer.
- /download/<filename> : Permet de télécharger un document PDF précédemment chargé.

Chaque route gère les méthodes GET et POST pour afficher les formulaires et traiter les soumissions.
"""
from flask import (
    Blueprint, render_template, request, Request, g, send_from_directory,
    session, url_for, redirect, jsonify
)
from werkzeug.datastructures import FileStorage
from models import User, DocToSigne, Signatures, Points, Invitation
from typing import Any, Dict, List
from os import getenv
from config import Config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from pathlib import Path
import shutil, logging, random, json, hmac, hashlib, smtplib


signatures_bp = Blueprint('signature', __name__, url_prefix='/signature')

ADMINISTRATION = 'ea.html'
BAD_INVITATION = 'Invitation invalide ou non trouvée.'

class SignatureDoer:
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
        if not self.document or not self.invitation or not self.points or not otp_valid:
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
        """Initialise avec l'objet request Flask."""
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

@signatures_bp.route('/deposer', methods=['GET', 'POST'])
def signature_make() -> Any:
    """
    Permet de déposer un document à signer.
    Méthodes supportées : GET, POST.
    GET : Affiche le formulaire de dépôt de document.
    POST : Traite le dépôt du document.
    """
    # === Gestion de l'envoi du formulaire en créant un document à signer ===
    if request.method == 'POST':
        # Récupération du formulaire
        # Récupérer les points de signature
        try:
            document = SignatureMaker(request) \
                            .get_request() \
                            .get_signature_points() \
                            .create_document() \
                            .create_points() \
                            .fix_documents() \
                            .send_invitation()
        except (IOError, FileNotFoundError) as e:
            message = f"Erreur lors du traitement du document : {str(e)}"
            return render_template(ADMINISTRATION, error_message=message)
        g.db_session.commit()
        message = f"Le document '{document.doc_to_signe.doc_nom}' a été créé et les invitations ont été envoyées."
        return redirect(url_for('ea', success_message=message))

    # === Affichage du formulaire de dépôt de document ===
    elif request.method == 'GET':
        users = g.db_session.query(User).order_by(User.nom).all()
        users = [user.to_dict(with_mdp=False) for user in users]
        return render_template(ADMINISTRATION, context='signature_make', users=users, document_name=None)
    
    # === Méthodes non autorisée ===
    else:
        return render_template(ADMINISTRATION, context=None, error_message="Méthode non autorisée")

@signatures_bp.route('/signer/<int:doc_id>/<hash_document>', methods=['GET', 'POST'])
def signature_do(doc_id: int, hash_document: str) -> Any:
    """
    Permet de signer un document.
    Méthodes supportées : GET, POST.
    GET : Affiche le formulaire de signature.
    POST : Traite la signature du document.
    """
    # === Gestion du formulaire de signature ===
    if request.method == 'POST':
        try:
            doer = SignatureDoer(request) \
                        .post_request(id_document=doc_id, hash_document=hash_document) \
                        .get_signature_points() \
                        .handle_signature_submission()
            
            g.db_session.commit()

            message = f"Le document '{doer.document.doc_nom}' a été signé avec succès."
            return jsonify(success=True, message=message, redirect=True)
        except ValueError as e:
            # En cas d'erreur (OTP erroné, etc.), retourner du JSON
            return jsonify(success=False, message=str(e)), 400
        except Exception as e:
            # En cas d'erreur système, retourner du JSON
            g.db_session.rollback()
            return jsonify(success=False, message="Erreur interne du serveur."), 500
    
    # === Affichage du formulaire de signature ===
    try:
        doer = SignatureDoer(request) \
                    .get_request(id_document=doc_id, hash_document=hash_document) \
                    .get_signature_points()
        
        # Sérialiser les points de signature en JSON pour éviter les erreurs de parsing JavaScript
        import json
        from datetime import datetime
        
        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, o: Any) -> Any:
                if isinstance(o, datetime):
                    return o.isoformat()
                return super().default(o)
        
        try:
            signature_points_json = json.dumps(doer.points, cls=CustomJSONEncoder)
        except (TypeError, ValueError):
            # En cas d'erreur de sérialisation, utiliser une liste vide
            signature_points_json = "[]"
        
        return render_template(ADMINISTRATION, context='signature_do', document=doer.document,
                               signature_points=doer.points, signature_points_json=signature_points_json,
                               curent_user_id=doer.signatory_id, hash_document=hash_document,
                               token=doer.token, curent_user_name=doer.signatory_name,
                               echeance=doer.invitation.expire_at)
    except ValueError:
        return render_template(ADMINISTRATION, error_message=BAD_INVITATION)

@signatures_bp.route('/<int:id_document>/otp/<hash_document>', methods=['POST'])
def signature_request_otp(id_document: int, hash_document: str) -> Any:
    """
    Permet de demander un code OTP pour signer un document.
    Méthodes supportées : POST.
    POST : Traite la demande de code OTP.
    """
    # Récupération de X-Invit-Token dans le header
    token = request.headers.get('X-Invit-Token', None)
    id_user = session.get('id', None)
    user = g.db_session.query(User).filter_by(id=id_user).first()
    invitation = g.db_session.query(Invitation) \
                        .filter_by(id_document=id_document, id_user=id_user, token=token) \
                        .first()
    document = g.db_session.query(DocToSigne) \
                        .filter_by(id=id_document, hash_fichier=hash_document) \
                        .first()
    if not invitation or not document:
        return jsonify(success=False, message=BAD_INVITATION), 400
    invitation.code_otp = str(random.randint(10000, 999999)).zfill(6)
    body_mail = render_template(
        'signatures/signature_otp_mail.html',
        nom_signataire=f'{user.prenom} {user.nom}'.strip(),
        otp_code=invitation.code_otp
    )
    try:
        send_otp_email(to=user.mail, template=body_mail)
        g.db_session.commit()
    except Exception as e:
        logging.error(f"Erreur lors de la création du code OTP : {e}")
        return jsonify(success=False, message="Erreur interne du serveur."), 500
    return jsonify(success=True)

@signatures_bp.route('/liste', methods=['GET'])
def signature_do_list() -> Any:
    """
    Permet d'afficher la liste des documents à signer,
    des documents signés et ceux dont la signature n'est pas allée au bout.
    Méthode supportée : GET.
    GET : Affiche la liste des documents.
    Filtrage côté client via JavaScript.
    """
    # Logique pour afficher la liste des documents à signer
    return render_template(ADMINISTRATION, context='signature_list')

@signatures_bp.route('/creer-depuis-modele', methods=['GET', 'POST'])
def create_signature_from_template() -> Any:
    """
    Permet de créer un document à signer depuis un modèle.
    Méthodes supportées : GET, POST.
    GET : Affiche le formulaire de création depuis un modèle.
    POST : Traite la création du document depuis un modèle.
    """
    if request.method == 'POST':
        # Logique pour créer un document à signer depuis un modèle
        pass
    return render_template(ADMINISTRATION, context='signature_create_from_template')

@signatures_bp.route('/upload', methods=['POST'])
def upload_document() -> Any:
    """
    Permet de charger un document PDF à signer.
    Méthodes supportées : POST.
    POST : Traite le chargement du document PDF.
    """
    if request.method == 'POST':
        pdf_document: FileStorage | None = request.files.get('pdf', None)
        filename = getattr(pdf_document, "filename", None)
        if not pdf_document or not filename:
            return render_template(ADMINISTRATION, error_message="Aucun document PDF téléchargé ou nom de fichier invalide.")
        elif filename.lower().endswith('.pdf'):
            # Nettoyer les fichiers expirés avant de créer un nouveau
            SecureDocumentAccess.cleanup_expired_temp_files()
            
            # Sauvegarde du fichier pdf
            filename = Path(filename).name
            
            # Sécuriser le nom de fichier
            folder_path = SecureDocumentAccess.TEMP_DIR
            
            # Vérifier que le dossier existe
            Path(folder_path).mkdir(parents=True, exist_ok=True)

            # Sauvegarder le fichier PDF
            file_path = f"{folder_path}/{filename}"
            pdf_document.save(file_path)
            
            # Générer le hash d'accès et créer le fichier temporaire
            document_hash = SecureDocumentAccess.generate_document_hash(filename)
            SecureDocumentAccess.create_temp_access_file(filename, document_hash)
            users = g.db_session.query(User).order_by(User.nom).all()
            users = [user.to_dict(with_mdp=False) for user in users]
            return render_template(ADMINISTRATION, context='signature_make',
                                   success_message="Document PDF téléchargé avec succès.",
                                   document_name=filename, users=users)
        else:
            return render_template(ADMINISTRATION, error_message="Le fichier téléchargé n'est pas un PDF.")
    else:
        return render_template(ADMINISTRATION, error_message="Méthode non autorisée.")
    
@signatures_bp.route('/download/<filename>')
def download_pdf(filename: str):
    """
    Permet de télécharger un document PDF précédemment chargé.
    Sécurisé par vérification d'accès via fichiers JSON temporaires ou points de signature.
    """
    temp_dir_param = request.args.get('temp_dir', 'false').lower()
    temp_dir: bool = temp_dir_param in ('true', '1', 'yes')
    
    # Vérifier l'accès via les fichiers temporaires
    if temp_dir:
        if not SecureDocumentAccess.verify_temp_access(filename):
            return "Accès non autorisé à ce document", 403
        
        folder_path = SecureDocumentAccess.TEMP_DIR
        return send_from_directory(folder_path, filename)
    
    # Vérifier l'accès via les points de signature (documents définitifs)
    else:
        id_user = session.get('id', None)
        if not id_user:
            return "Session utilisateur non valide", 401
        
        # Rechercher les points de signature pour ce fichier et cet utilisateur
        points = g.db_session.query(Points).join(DocToSigne, DocToSigne.id == Points.id_document) \
                    .filter(Points.id_user == id_user) \
                    .filter(
                        (DocToSigne.doc_nom == filename) |
                        (DocToSigne.chemin_fichier.like(f'%/{filename}')) |
                        (DocToSigne.chemin_fichier.like(f'%\\{filename}')) |
                        (DocToSigne.chemin_fichier.endswith(filename))
                    ).all()
        
        if not points:
            return "Accès non autorisé à ce document", 403
        
        # Récupérer le chemin réel du fichier depuis la base de données
        document = points[0].document
        real_file_path = Path(document.chemin_fichier)
        
        if not real_file_path.exists():
            return "Fichier non trouvé", 404
        
        # Servir le fichier depuis son emplacement réel
        folder_path = str(real_file_path.parent)
        filename_real = real_file_path.name
        
        return send_from_directory(folder_path, filename_real)
