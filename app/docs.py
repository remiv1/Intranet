from flask import jsonify, send_file
from werkzeug.utils import secure_filename
import os, io, datetime, paramiko
from app import __init__, app, impression

#Définition des variables de gestion
HOSTNAME = app.config["SSH_HOST"]
PORT = app.config["SSH_PORT"]
USERNAME = app.config["SSH_USER"]
PASSWORD = app.config["SSH_PASSWORD"]
FOLDER = app.config["UPLOAD_FOLDER"]
PRINT_FOLDER = app.config["PRINT_PATH"]

#Validation des chemins
if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)

#Connexion au serveur SSH
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOSTNAME=HOSTNAME, port=PORT, username=USERNAME, password=PASSWORD)

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
        file_path = folder + secure_filename(file_name) + extension
        
        #Transfert du fichier vers le serveur
        sftp = client.open_sftp()
        with sftp.file(file_path, 'wb') as remote_file:
            remote_file.write(file.read())
        sftp.close()
        
        return jsonify({'message': 'File uploaded successfully'})
    
    except TypeError as te:
        return jsonify({'erreur': f'Erreur de typage de fichier : {te}'})
    except paramiko.SSHException as se:
        return jsonify({'erreur': f'Erreur SSH : {se}'})
    except IOError as ie:
        return jsonify({'erreur': f'Erreur d\'entrée/sortie : {ie}'})
    except Exception as e:
        return jsonify({'erreur': f'Erreur inconnue : {e}'})
    
#Téléchargement du fichier depuis le serveur
def download_file(file_name: str, extension: str):
    
    try:
        #Création du chemin du fichier sur le serveur
        remote_file_path = os.path.join(folder, secure_filename(file_name) + '.' + extension)

        #Transfert du fichier depuis le serveur
        sftp = client.open_sftp()
        with sftp.open(remote_file_path, 'rb') as remote_file:
            file_data = remote_file.read()
        sftp.close()

        #Création d'un objet pour envoyer le fichier au client
        file_stream = io.BytesIO(file_data)
        file_stream.seek(0)

        return send_file(file_stream, as_attachment=True, download_name=secure_filename(file_name) + '.' + extension)
    
    except paramiko.SSHException as se:
        return jsonify({'erreur': f'Erreur SSH : {se}'})
    except IOError as ie:
        return jsonify({'erreur': f'Erreur d\'entrée/sortie : {ie}'})
    except Exception as e:
        return jsonify({'erreur': f'Erreur inconnue : {e}'})
    
def delete_file(file_name: str, extension: str):
    
    try:
        #Création du chemin du fichier sur le serveur
        file_path = folder + secure_filename(file_name) + '.' + extension
        
        #Suppression du fichier sur le serveur
        sftp = client.open_sftp()
        sftp.remove(file_path)
        sftp.close()
        
        return jsonify({'message': 'File deleted successfully'})
    
    except paramiko.SSHException as se:
        return jsonify({'erreur': f'Erreur SSH : {se}'})
    except IOError as ie:
        return jsonify({'erreur': f'Erreur d\'entrée/sortie : {ie}'})
    except Exception as e:
        return jsonify({'erreur': f'Erreur inconnue : {e}'})
    
def print_document(file: io.BytesIO, file_name: str, extension: str, copies: str, username: str, sides: str, media: str, orientation: str, color: str):
    
    try:
        #Création du chemin du fichier sur le serveur
        file_path = print_folder + secure_filename(file_name) + '.' + extension
        
        #Transfert du fichier vers le serveur
        sftp = client.open_sftp()
        with sftp.file(file_path, 'wb') as remote_file:
            remote_file.write(file.read())
        sftp.close()
        
        #Impression du fichier
        impression.print_file(file_path, username, 'Intranet' , copies, sides, media, orientation, color)
        os.remove(file_path)
        
        return jsonify({'message': 'File printed successfully'})
    
    except paramiko.SSHException as se:
        return jsonify({'erreur': f'Erreur SSH : {se}'})
    except IOError as ie:
        return jsonify({'erreur': f'Erreur d\'entrée/sortie : {ie}'})
    except Exception as e:
        return jsonify({'erreur': f'Erreur inconnue : {e}'})