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
from flask import Blueprint, render_template, request, Request, g, send_from_directory, session
from werkzeug.datastructures import FileStorage
from models import User, DocToSigne, Signatures, Points
from typing import Any, Dict
from os import getenv
import hashlib
import hmac
import json
from datetime import datetime
from pathlib import Path
import shutil

signatures_bp = Blueprint('signature', __name__, url_prefix='/signature')

ADMINISTRATION = 'ea.html'

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
        for json_file in temp_dir.glob("*.json"):
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
                if datetime.now().timestamp() > expires_at:
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
            _ = SignatureMaker(request) \
                            .get_request() \
                            .get_signature_points() \
                            .create_document() \
                            .create_points() \
                            .fix_documents()
        except (IOError, FileNotFoundError) as e:
            return render_template(ADMINISTRATION, error_message=str(e))
        g.db_session.commit()
        return render_template(ADMINISTRATION,
                               success_message="Document à signer créé avec succès.")

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
    if request.method == 'POST':
        # Logique pour signer un document
        pass
    return render_template(ADMINISTRATION, context='signature_do', doc_id=doc_id, hash_document=hash_document)

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
    Sécurisé par vérification d'accès via fichiers JSON temporaires.
    """
    temp_dir: bool = bool(request.args.get('temp_dir', False)) or False
    # Vérifier l'accès via les fichiers temporaires
    if not SecureDocumentAccess.verify_temp_access(filename):
        return "Accès non autorisé à ce document", 403
    
    # Accès autorisé, servir le fichier
    folder_path = SecureDocumentAccess.TEMP_DIR if temp_dir else getenv('SIGNATURE_DOCKER_PATH', '/tmp/')
    return send_from_directory(folder_path, filename)
