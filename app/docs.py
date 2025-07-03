from flask import jsonify, send_file
from werkzeug.utils import secure_filename
import os, io, datetime, paramiko
from app import __init__, app#, impression

#Définition des variables de gestion
_HOSTNAME = app.config["SSH_HOST"]
_PORT = app.config["SSH_PORT"]
_USERNAME = app.config["SSH_USER"]
_PASSWORD = app.config["SSH_PASSWORD"]
_FOLDER = app.config["UPLOAD_FOLDER"]
_PRINT_FOLDER = app.config["PRINT_PATH"]

#Validation des chemins
if not os.path.exists(_FOLDER):
    os.makedirs(_FOLDER)

#Création d'un nom de docment
def create_name(doc_date: str, idContrat: str, idDocument: str, SType: str):
    date_date = datetime.datetime.strptime(doc_date, '%Y-%m-%d')
    str_date = date_date.strftime('%d%m%Y')
    str_idContrat = str(idContrat).zfill(3)
    str_idDocument = str(idDocument).zfill(4)
    str_SType = SType[:5]
    retour = f'{str_date}_{str_idContrat}_{str_idDocument}_{str_SType}'
    return retour


#Téléchargement du fichier vers le serveur
def upload_file(file: io.BytesIO, file_name: str, extension: str):

    try:
        #Création du chemin du fichier sur le serveur
        file_name = secure_filename(file_name) + '.' + extension
        file_path = os.path.join(_FOLDER, file_name)
        
        # Enregistrement du fichier sur le serveur
        with open(file_path, 'wb') as f:
            f.write(file.read())

        return jsonify({'message': 'File uploaded successfully'})
    
    except Exception as e:
        return jsonify({'erreur': f'Erreur lors de la sauvegarde locale : {e}'})
    
#Téléchargement du fichier depuis le serveur
def download_file(file_name: str, extension: str):
    
    try:
        #Création du chemin du fichier sur le serveur
        remote_file_path = os.path.join(_FOLDER, secure_filename(file_name) + '.' + extension)

        #Transfert du fichier depuis le serveur
        with open(remote_file_path, 'rb') as f:
            file_data = f.read()

        #Création d'un objet pour envoyer le fichier au client
        file_stream = io.BytesIO(file_data)
        file_stream.seek(0)

        return send_file(file_stream, as_attachment=True, download_name=secure_filename(file_name) + '.' + extension)
    
    except FileNotFoundError:
        return jsonify({'erreur': f'Erreur de fichier introuvable : {file_name}.{extension}'}), 404
    except Exception as e:
        return jsonify({'erreur': f'Erreur inconnue lors du téléchargement : {e}'})
    
def delete_file(file_name: str, extension: str):
    
    try:
        #Création du chemin du fichier sur le serveur
        file_name = secure_filename(file_name) + '.' + extension
        file_path = os.path.join(_FOLDER, file_name)

        #Suppression du fichier sur le serveur
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'Fichier supprimé avec succès'})
        else:
            return jsonify({'erreur': f'Erreur lors de la suppression : {file_name}, {e}'})

    except Exception as e:
        return jsonify({'erreur': f'Erreur inconnue : {e}'})
    
def print_document(file: io.BytesIO, file_name: str, extension: str, copies: str, username: str, sides: str, media: str, orientation: str, color: str):
    
    try:
        #Création du chemin du fichier sur le serveur
        file_name = secure_filename(file_name) + '.' + extension
        file_path = os.path.join(_PRINT_FOLDER, file_name)
        
        #Transfert du fichier vers le serveur
        with open(file_path, 'wb') as f:
            f.write(file.read())
        
        #Impression du fichier
        impression.print_file(file_path, username, 'Intranet' , copies, sides, media, orientation, color)
        os.remove(file_path)
        
        return jsonify({'message': 'Document imprimé avec succès'})
    
    except Exception as e:
        return jsonify({'erreur': f'Erreur lors de l\'impression : {e}'})