"""
Blueprint pour la gestion de services de signature électronique.

Routes:
- /signature/deposer : Permet de déposer un document à signer.
- /signature/signer/<doc_id>/<hash_document> : Permet de signer un document.

Chaque route gère les méthodes GET et POST pour afficher les formulaires et traiter les soumissions.
"""
from flask import Blueprint, render_template, request, g, send_from_directory
from werkzeug.datastructures import FileStorage
from models import User
from typing import Any
from os import getenv

signatures_bp = Blueprint('signature', __name__, url_prefix='/signature')

ADMINISTRATION = 'ea.html'

@signatures_bp.route('/deposer', methods=['GET', 'POST'])
def signature_make() -> Any:
    if request.method == 'POST':
        # Logique pour traiter le dépôt du document
        pass
    elif request.method == 'GET':
        users = g.db_session.query(User).order_by(User.name).all()
        return render_template(ADMINISTRATION, context='signature_make', users=users)
    else:
        return render_template(ADMINISTRATION, context=None, error_message="Méthode non autorisée")

@signatures_bp.route('/signer/<int:doc_id>/<hash_document>', methods=['GET', 'POST'])
def signature_do(doc_id: int, hash_document: str) -> Any:
    if request.method == 'POST':
        # Logique pour signer un document
        pass
    return render_template(ADMINISTRATION, context='signature_do', doc_id=doc_id, hash_document=hash_document)

@signatures_bp.route('/liste', methods=['GET'])
def signature_do_list() -> Any:
    # Logique pour afficher la liste des documents à signer
    return render_template(ADMINISTRATION, context='signature_list')

@signatures_bp.route('/creer-depuis-modele', methods=['GET', 'POST'])
def create_signature_from_template() -> Any:
    if request.method == 'POST':
        # Logique pour créer un document à signer depuis un modèle
        pass
    return render_template(ADMINISTRATION, context='signature_create_from_template')

@signatures_bp.route('/charger-pdf', methods=['POST'])
def upload_document() -> Any:
    if request.method == 'POST':
        pdf_document: FileStorage | None = request.files.get('pdf', None)
        filename = getattr(pdf_document, "filename", None)
        if not pdf_document or not filename:
            return render_template(ADMINISTRATION, error_message="Aucun document PDF téléchargé ou nom de fichier invalide.")
        elif filename.lower().endswith('.pdf'):
            # Sauvegarde du fichier pdf et récupération de son chemin
            folder_path = getenv('SIGNATURE_DOCKER_PATH', '/tmp/')
            file_path = f"{folder_path}/{filename}"
            pdf_document.save(file_path)
            return render_template(ADMINISTRATION, context='signature_make',
                                   success_message="Document PDF téléchargé avec succès.",
                                   document_name=filename)
        else:
            return render_template(ADMINISTRATION, error_message="Le fichier téléchargé n'est pas un PDF.")
    else:
        return render_template(ADMINISTRATION, error_message="Méthode non autorisée.")
    
@signatures_bp.route('/download/<filename>')
def download_pdf(filename: str):
    folder_path = getenv('SIGNATURE_DOCKER_PATH', '/tmp/')
    return send_from_directory(folder_path, filename)
