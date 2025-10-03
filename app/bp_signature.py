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
# Imports Flask/Werkzeug
from flask import (
    Blueprint, render_template, request, g, send_from_directory,
    session, url_for, redirect, jsonify
)
from werkzeug.datastructures import FileStorage
# Imports locaux
from models import User, DocToSigne, Points, Invitation
from signatures import SignatureDoer, SignatureMaker, SecureDocumentAccess, SignedDocumentCreator, send_otp_email
# Imports standards
from typing import Any
from pathlib import Path
import logging, random

signatures_bp = Blueprint('signature', __name__, url_prefix='/signature')

ADMINISTRATION = 'ea.html'
BAD_INVITATION = 'Invitation invalide ou non trouvée.'
INTERNAL_SERVER_ERROR = 'Erreur interne du serveur.'

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
            return jsonify(success=False, message=INTERNAL_SERVER_ERROR), 500
    
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
        return jsonify(success=False, message=INTERNAL_SERVER_ERROR), 500
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

@signatures_bp.route('/creer/<int:id_document>/<hash_document>', methods=['POST'])
def create_final_signed_document(id_document: int, hash_document: str) -> Any:
    """
    Permet de créer le document final signé (PDF) après que tous les signataires ont signé.
    Méthode supportée : POST.
    POST : Traite la création du document final signé.
    """
    try:
        # Récupérer l'ID de l'utilisateur courant
        current_user_id = session.get('id', None)
        if not current_user_id:
            return jsonify(success=False, message="Session utilisateur invalide."), 401
        
        # Créer et exécuter le processus de création du document signé
        creator = SignedDocumentCreator(
            id_document=id_document
        )
        
        # Exécuter toutes les étapes du processus
        creator.load_document(hash_document=hash_document) \
               .verify_document_integrity() \
               .load_signatures_and_points() \
               .verify_all_signatures_completed() \
               .apply_signatures_to_pdf() \
               .add_signature_certificates() \
               .save_final_document() \
               .send_signed_document_by_email()
        
        # Sauvegarder les modifications en base
        g.db_session.commit()
        
        # Retourner une réponse de succès
        document_name = creator.document.doc_nom if creator.document else "Document"
        return jsonify(
            success=True, 
            message=f"Le document '{document_name}' a été finalisé et envoyé par email avec succès.",
            document_id=id_document
        )
        
    except ValueError as e:
        # Erreurs métier (droits, intégrité, etc.)
        return jsonify(success=False, message=str(e)), 400
        
    except FileNotFoundError as e:
        # Erreurs de fichier
        return jsonify(success=False, message=f"Fichier non trouvé : {str(e)}"), 404
        
    except Exception as e:
        # Erreurs système
        logging.error(f"Erreur lors de la création du document final signé : {e}")
        g.db_session.rollback()
        return jsonify(success=False, message=INTERNAL_SERVER_ERROR), 500

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
