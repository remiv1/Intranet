from flask import Flask, render_template, Request, request, redirect, url_for, session, g
from flask.typing import ResponseReturnValue
from werkzeug import Response
from config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from app.models import Base
from app import docs
from app.models import User, Contract, Event, Document
from typing import List, Dict, Any, cast, Optional, Tuple
import hashlib
import datetime
import os
from datetime import timedelta

app = Flask(__name__)

# Charger la configuration depuis config.py
app.config.from_object(Config)

# Construction de l'URL de la base de données
db_user: str = cast(str, app.config["DB_USER"])
db_password: str = cast(str, app.config["DB_PASSWORD"])
db_host: str = cast(str, app.config["DB_HOST"])
db_name: str = cast(str, app.config["DB_NAME"])
db_url = URL.create(
    drivername="mysql+mysqlconnector",
    username=db_user,
    password=db_password,
    host=db_host,
    port=3306,
    database=db_name,
    query={"charset": "utf8mb4"}
)

# Créer l'engin SQLAlchemy
engine = create_engine(db_url,
                        pool_recycle=1800,
                        pool_timeout=30,
                        pool_pre_ping=True,
                        connect_args={'connect_timeout': 10},
                        echo=True)

# Créer les tables de la base de données
Base.metadata.create_all(engine)

# Créer une session de base de données
Session = sessionmaker(bind=engine)

# Création des constantes
UPLOAD_EXTENSIONS = ['.jpg', '.png', '.gif', '.jpeg', '.tif', '.tiff', '.pdf']
RESERVED_SPACE = 'Espace réservé'

# Configuration de l'application
app.config['UPLOAD_EXTENSIONS'] = UPLOAD_EXTENSIONS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

def get_user_from_credentials(request_form: Request) -> Tuple[User | None, str, str]:
    # Récupération du credential
    username = request_form.form.get('username', '')
    password = request_form.form.get('password', '')
    password = hashlib.sha256(password.encode()).hexdigest()

    try:
        # Recherche de l'utilisateur dans la base de données
        user = g.db_session.query(User).filter(User.identifiant == username).first()

    except Exception:
        # Gérer les exceptions potentielles
        user = None

    # Retourne les identifiants de l'utilisateur et l'utilisateur
    return user, username, password

def valid_authentication(user: User, password: str) -> bool:
    if user and user.shaMdp == password:
        session['identifiant'] = user.identifiant
        session['prenom'] = user.prenom
        session['nom'] = user.nom
        session['mail'] = user.mail
        session['habilitation'] = user.habilitation
        try:
            # Stocker les informations de l'utilisateur dans la session
            user.falseTest=0
            g.db_session.commit()
            return True
        except Exception:
            g.db_session.rollback()
            return False
    return False

def generate_nb_false_pwd(user: User) -> str:
    if user.falseTest < 2:
        user.falseTest += 1
        reste = 3 - user.falseTest
        message = f'Erreur d\'identifiant ou de mot de passe, il vous reste {reste} essais.'
    else:
        user.locked = True
        user.falseTest = 3
        message = f'Utilisateur {user.nom} vérouillé, merci de contacter votre administrateur.'
    try:
        g.db_session.commit()
    except Exception as e:
        g.db_session.rollback()
        message = f'Erreur lors de la mise à jour du compteur d\'essais : {e}'
    return message


@app.before_request
def before_request() -> None:
    g.db_session = Session()

@app.teardown_appcontext
def teardown_request(exception: Optional[BaseException]):
    db_session = g.pop('db_session', None)
    if db_session is not None:
        if exception:
            db_session.rollback()
        db_session.close()

@app.route('/')
def home() -> str | Response:
    if 'prenom' in session and 'nom' in session:
        prenom = session['prenom']
        nom = session['nom']
        habilitation = session['habilitation']
        
        # création d'une liste de niveaux d'habilitation
        habilitation_levels = list(map(int, str(habilitation)))

        sections: List[Dict[str, Any]] = [
            {
                'classe': 1,
                'titre': 'Gestion des droits',
                'descriptif': 'Permet de gérer/créer/supprimer les droits des utilisateurs de l\'Intranet',
                'buttonid': 'Gdr',
                'onclick': 'gestion_droits'
            },
            {
                'classe': 2,
                'titre': 'Gestion des utilisateurs',
                'descriptif': 'Permet de gérer les utilisateurs déjà existant de l\'Intranet',
                'buttonid': 'Gdu',
                'onclick': 'gestion_utilisateurs'
            },
            {
                'classe': 2,
                'titre': 'Gestion des contrats',
                'descriptif': 'Permet de gérer/accéder aaux contrats en cours pour l\'établissement et d\'en gérer les documents et évènements',
                'buttonid': 'Ddc',
                'onclick': 'contrats'
            },
            {
                'classe': 3,
                'titre': RESERVED_SPACE,
                'descriptif': 'Espace réservé pour les professeurs principaux des classes (en construction)',
                'buttonid': 'Erpp',
                'onclick': 'erpp'
            },
            {
                'classe': 4,
                'titre': RESERVED_SPACE,
                'descriptif': 'Espace réservé pour les professeurs de l\'établissement (en construction)',
                'buttonid': 'Erp',
                'onclick': 'erp'
            },
            {
                'classe': 6,
                'titre': 'Espace impressions',
                'descriptif': 'Espace de lancement des impressions à distance',
                'buttonid': 'Ei',
                'onclick': 'ei'
            },
            {
                'classe': 5,
                'titre': RESERVED_SPACE,
                'descriptif': 'Espace réservé pour les élèves de l\'établissement (en construction)',
                'buttonid': 'Ere',
                'onclick': 'ere'
            }
        ]

        return render_template('index.html', prenom=prenom, nom=nom, habilitation_levels=habilitation_levels, sections=sections)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login() -> Response | str:
    message = request.args.get('message', '')

    if request.method == 'POST':
        try:
            # récupération du contenu du formulaire
            user, username, password = get_user_from_credentials(request)

            # Vérifier si l'utilisateur existe et si le mot de passe est correct
            if valid_authentication(user, password):
                return redirect(url_for('home'))
            
            # Gestion de l'absence d'utilisateur
            elif not user:
                message = f'L\'utilisateur {username} semble inconnu'
            
            # Gestion des erreurs de mots de passe
            else:
                message = generate_nb_false_pwd(user)

            # Rediriger vers la page de connexion avec le message approprié
            return redirect(url_for('login', message=message))
        except Exception as e:
            # En cas d'erreur, retour sur la page de connexion après rollback
            g.db_session.rollback()
            message = f'Erreur lors de la connexion, veuillez réessayer : {e}'
            return redirect(url_for('login', message=message))

    # Gestion de la méthode GET (affichage de la page de connexion)
    else:
        return render_template('login.html', message=message)

@app.route('/logout')
def logout() -> Response:
    session.clear()
    return redirect(url_for('login'))

@app.route('/gestion_droits')
def gestion_droits() -> str | Response:
    if '1' in str(session['habilitation']): 
        users = g.db_session.query(User).all()
        return render_template('gestion_droits.html', users=users)
    else:
        return redirect(url_for('logout'))

@app.route('/gestion_utilisateurs')
def gestion_utilisateurs() -> str | Response:
    if '2' in str(session['habilitation']): 
        users: list[User] = g.db_session.query(User).all()
        users.sort(key=lambda x: (x.nom, x.prenom))
        return render_template('gestion_utilisateurs.html', users=users)
    else:
        return redirect(url_for('logout'))

@app.route('/gestion_documents')
def gestion_documents() -> str | Response:
    if '2' in str(session['habilitation']):
        return render_template('gestion_documents.html')
    else:
        return redirect(url_for('logout'))

@app.route('/erpp')
def erpp() -> str | Response:
    if '3' in str(session['habilitation']):
        return render_template('erpp.html')
    else:
        return redirect(url_for('logout'))

@app.route('/erp')
def erp() -> str | Response:
    if '4' in str(session['habilitation']): 
        return render_template('erp.html')
    else:
        return redirect(url_for('logout'))

@app.route('/ei')
def ei() -> str | Response:
    if '6' in str(session['habilitation']):
        return render_template('ei.html')
    else:
        return redirect(url_for('logout'))

@app.route('/print_doc', methods=['POST'])
def print_doc() -> Response:
    if '6' in str(session['habilitation']):
        binary_document: Any = request.files['document']
        document = str(binary_document.filename)
        extension: str = str(os.path.splitext(document))[1]
        docname = document.split('.')[0]
        username = session['prenom'] + ' ' + session['nom']
        copies: str = str(request.form.get('copies'))
        sides: str = request.form.get('recto_verso', '')
        media: str = request.form.get('format', '')
        orientation: str = request.form.get('orientation', '')
        color: str = request.form.get('couleur', '')

        #Envoi du document à l'imprimante
        docs.print_document(binary_document,docname, extension, copies, username, sides, media, orientation, color)

        #Suppression du document sur le serveur
        docs.delete_file(docname, extension)

        return redirect(url_for('ei', message='Impression envoyée'))
    else:
        return redirect(url_for('logout'))

@app.route('/ere')
def ere() -> str | Response:
    if '5' in str(session['habilitation']):
        return render_template('ere.html')
    else:
        return redirect(url_for('logout'))

@app.route('/ajout_utilisateurs', methods=['POST'])
def ajout_utilisateurs() -> Response:
    if '1' in str(session['habilitation']): 
        try:
            #Récupération des données du formulaire
            prenom = request.form.get('prenom')
            nom = request.form.get('nom')
            mail = request.form.get('mail')
            identifiant = request.form.get('identifiant')
            mdp = request.form.get('mdp', '')
            mdp = hashlib.sha256(mdp.encode()).hexdigest()

            #Création du niveau d'habilitation
            habilitation_values: List[str] = []
            for key, value in request.form.items():
                if key.startswith('habil'):
                    habilitation_values.append(value)
        
            #Trier les valeurs d'habilitation
            sorted_habil = sorted(habilitation_values, key=int)

            #Concaténation des valeurs d'habilitation
            habilitation = int(''.join(sorted_habil))

            user = User(prenom=prenom, nom=nom, identifiant=identifiant, mail=mail, habilitation=habilitation, shaMdp=mdp)
            g.db_session.add(user)
            g.db_session.commit()

            return redirect(url_for('gestion_utilisateurs'))
        except Exception:
            g.db_session.rollback()
            return redirect(url_for('gestion_utilisateurs'))
    else: 
        return redirect(url_for('logout'))

@app.route('/suppr_utilisateurs', methods=['POST'])
def suppr_utilisateurs() -> Response:
    if '1' in str(session['habilitation']): 
        try:
            identifiant = request.form.get('identifiant')
            user = g.db_session.query(User).filter(User.identifiant == identifiant).first()
            if user:
                g.db_session.delete(user)
                g.db_session.commit()
            return redirect(url_for('gestion_utilisateurs'))
        except Exception:
            g.db_session.rollback()
            return redirect(url_for('gestion_utilisateurs'))
    else:
        return redirect(url_for('logout'))

@app.route('/modif_utilisateurs', methods=['POST'])
def modif_utilisateurs() -> Response:
    if '1' in str(session['habilitation']) or '2' in str(session['habilitation']): 
        try:
            prenom = request.form.get('prenom', '')
            nom = request.form.get('nom', '')
            mail = request.form.get('mail', '')
            identifiant = request.form.get('identifiant', '')
            mdp = request.form.get('mdp', '')
            mdp = hashlib.sha256(mdp.encode()).hexdigest()
            if request.form.get('unlock'):
                unlock = int(request.form.get('unlock', 0))
            else:
                unlock = 0

            #Création du niveau d'habilitation
            habilitation_values: List[str] = []
            for key, value in request.form.items():
                if key.startswith('habil'):
                    habilitation_values.append(value)

            #Trier les valeurs d'habilitation
            sorted_habil = sorted(habilitation_values, key=int)

            #Concaténation des valeurs d'habilitation
            habilitation = int(''.join(sorted_habil))

            #Récupération de l'utilisateur
            user = g.db_session.query(User).filter(User.identifiant == identifiant).first()

            if user:
                # Modification des informations de l'utilisateur
                user.prenom = prenom
                user.nom = nom
                user.mail = mail
                user.identifiant = identifiant
                if mdp != '': 
                    user.shaMdp = mdp
                
                if unlock == 1:
                    user.falseTest = 0
                    user.locked = False

                user.habilitation = habilitation

                g.db_session.commit()

            return redirect(url_for('gestion_utilisateurs'))
        except Exception:
            g.db_session.rollback()
            return redirect(url_for('gestion_utilisateurs'))
    else:
        return redirect(url_for('logout'))

@app.route('/gestion_droits', methods=['POST'])
def gestion_droits_post() -> Response:
    if '1' in str(session['habilitation']) or '2' in str(session['habilitation']): 
        try:
            identifiant = request.form.get('identifiant', '')
            mdp = request.form.get('mdp', '')
            mdp = hashlib.sha256(mdp.encode()).hexdigest()
            
            #Création du niveau d'habilitation
            habilitation_values: List[str] = []
            for key, value in request.form.items():
                if key.startswith('habil'):
                    habilitation_values.append(value)
            
            #Trier les valeurs d'habilitation
            sorted_habil = sorted(habilitation_values, key=int)

            #Concaténation des valeurs d'habilitation
            habilitation = int(''.join(sorted_habil))

            user = g.db_session.query(User).filter(User.identifiant == identifiant).first()
            if user:
                if mdp != '':
                    user.shaMdp = mdp
                user.habilitation = habilitation

                g.db_session.commit()

            return redirect(url_for('gestion_droits'))
        except Exception as e:
            g.db_session.rollback()
            return redirect(url_for('gestion_droits'))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats', methods=['GET', 'POST'])
def contrats() -> ResponseReturnValue:
    if '2' in str(session['habilitation']):
        if request.method == 'GET':
            contracts = g.db_session.query(Contract).all()
            return render_template('contrats.html', contracts=contracts)
        
        elif request.method == 'POST':
            try:
                #Récupération des données du formulaire*
                type_contrat = request.form.get('Type0', '')
                sous_type_contrat = request.form.get('SType0', '')
                entreprise = request.form.get('Entreprise', '')
                num_contrat_externe = request.form.get('numContratExterne', '')
                intitule = request.form.get('Intitule', '')
                date_debut = request.form.get('dateDebut', '')
                date_fin_preavis = request.form.get('dateFinPreavis', '')
                date_fin = request.form.get('dateFin', '')

                if date_fin != '': 
                    contract = Contract(Type = type_contrat,
                                        SType = sous_type_contrat,
                                        entreprise = entreprise,
                                        numContratExterne = num_contrat_externe,
                                        intitule = intitule,
                                        dateDebut = date_debut,
                                        dateFin = date_fin,
                                        dateFinPreavis = date_fin_preavis)
                else:
                    contract = Contract(Type = type_contrat,
                                        SType = sous_type_contrat,
                                        entreprise = entreprise,
                                        numContratExterne = num_contrat_externe,
                                        intitule = intitule,
                                        dateDebut = date_debut,
                                        dateFinPreavis = date_fin_preavis)

                g.db_session.add(contract)
                g.db_session.commit()

                return redirect(url_for('contrats'))
            except Exception:
                g.db_session.rollback()
                return redirect(url_for('contrats'))
        else:
            return redirect(url_for('contrats'))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/<numContrat>', methods=['GET', 'POST'])
def contrats_by_num(numContrat: int) -> ResponseReturnValue:
    if request.method == 'GET': 
        contract = g.db_session.query(Contract).filter(Contract.id == numContrat).first()
        events = g.db_session.query(Event).filter(Event.idContrat == numContrat)
        documents = g.db_session.query(Document).filter(Document.idContrat == numContrat)

        return render_template('contrat_detail.html', contract = contract, events = events, documents = documents)
    elif request.method == 'POST' and request.form.get('_method') == 'PUT':
        try:
            contract = g.db_session.query(Contract).filter(Contract.id == numContrat).first()
            if contract:
                contract.Type = request.form.get(f'Type{numContrat}')
                contract.SType = request.form.get(f'SType{numContrat}')
                contract.Entreprise = request.form.get(f'Entreprise{numContrat}')
                contract.numContratExterne = request.form.get(f'numContratExterne{numContrat}')
                contract.Intitule = request.form.get(f'Intitule{numContrat}')
                contract.dateDebut = request.form.get(f'dateDebut{numContrat}')
                contract.dateFinPreavis = request.form.get(f'dateFinPreavis{numContrat}')
                if request.form.get(f'dateFin{numContrat}') != '':
                    contract.dateFin = request.form.get(f'dateFin{numContrat}')
            
                g.db_session.commit()

            return redirect(url_for('contrats'))
        except Exception:
            g.db_session.rollback()
            return redirect(url_for('contrats'))
    else:
        return redirect(url_for('contrats'))

@app.route('/contrats/<numContrat>/evenement', methods=['POST'])
def add_contrats_event(numContrat: int) -> ResponseReturnValue:
    if '2' in str(session['habilitation']):
        if request.method == 'POST':
            try:
                #Récupération des données du formulaire*
                idContrat = request.form.get('idContratE')
                dateEvenement = request.form.get('dateEvenementE')
                Type = request.form.get('TypeE0')
                SType = request.form.get('STypeE0')
                descriptif = request.form.get('descriptifE')

                event = Event(idContrat = idContrat, dateEvenement = dateEvenement, Type = Type, SType = SType, descriptif = descriptif)
                
                g.db_session.add(event)
                g.db_session.commit()

                return redirect(url_for('contrats_by_num', numContrat=idContrat))
            except Exception:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat=numContrat))
        else:
            return redirect(url_for('contrats_by_num', numContrat=numContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/<numContrat>/document', methods=['POST'])
def add_contrats_document(numContrat: int) -> ResponseReturnValue:
    if '2' in str(session['habilitation']):
        if request.method == 'POST':
            try:
                #Récupération du dernier élément
                last_doc = g.db_session.query(Document).order_by(Document.id.desc()).first()
                if last_doc:
                    id = str(last_doc.id + 1)
                else:
                    id = '1'

                #Récupération des données du formulaire
                id_contrat = request.form.get('idContratD', '')
                date_document = request.form.get('dateDocumentD', '')
                type_document = request.form.get('TypeD0', '')
                sous_type_document = request.form.get('STypeD0', '')
                descriptif = request.form.get('descriptifD', '')
                document_binaire: Any = request.files['documentD']
                extention: str = os.path.splitext(str(document_binaire.filename))[1]
                name = docs.create_name(date_document, id_contrat, id, sous_type_document)
                lien_document = name + extention

                #Création du document dans la base de données
                document = Document(idContrat = id_contrat,
                                    Type = type_document,
                                    SType = sous_type_document,
                                    descriptif = descriptif,
                                    strLien = lien_document,
                                    dateDocument = date_document,
                                    name = name)

                #Ajout et Fermeture de la session
                g.db_session.add(document)
                g.db_session.commit()

                #Enregistrement du fichier sur le serveur
                docs.upload_file(document_binaire, name, extention)

                #Retour du formulaire
                return redirect(url_for('contrats_by_num', numContrat=id_contrat))
            except Exception:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat=numContrat))
        else:
            return redirect(url_for('contrats_by_num', numContrat=numContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/numContrat/<numContrat>/numEvenement/<numEvent>', methods=['POST'])
def modif_event_id(numEvent, numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST' and request.form.get('_method') == 'PUT':
            try:
                #Récupération de l'évènement
                event = g.db_session.query(Event).filter(Event.id == numEvent).first()

                if event:
                    #Récupération formulaire
                    idContrat = request.form.get(f'idContratE{numEvent}')
                    event.idContrat = request.form.get(f'idContratE{numEvent}')
                    event.dateEvenement = request.form.get(f'dateEvenementE{numEvent}')
                    event.Type = request.form.get(f'TypeE{numEvent}')
                    event.SType = request.form.get(f'STypeE{numEvent}')
                    event.descriptif = request.form.get(f'descriptifE{numEvent}')

                    #Retour
                    g.db_session.commit()

                    return redirect(url_for('contrats_by_num', numContrat = idContrat))
            except Exception as e:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat = numContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/numContrat/<numContrat>/numDocument/<numDoc>', methods=['POST'])
def modif_document_id(numDoc, numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST' and request.form.get('_method') == 'PUT':
            try:
                #Récupération du document
                document = g.db_session.query(Document).filter(Document.id == numDoc).first()

                if document:
                    #Récupération formulaire
                    id = document.id
                    idContrat = request.form.get(f'idContratD{numDoc}')
                    dateDocument = request.form.get(f'dateDocumentD{numDoc}')
                    document.dateDocument = dateDocument
                    Type = request.form.get(f'TypeD{numDoc}')
                    document.Type = Type
                    SType = request.form.get(f'STypeD{numDoc}')
                    document.SType = SType
                    document.descriptif = request.form.get(f'descriptifD{numDoc}')
                    if request.files[f'documentD{numDoc}']:
                        DocumentBinaire = request.files[f'documentD{numDoc}']
                        name = docs.create_name(dateDocument, idContrat, id, SType)
                        extention = os.path.splitext(DocumentBinaire.filename)[1]
                    else:
                        strLien = request.form.get(f'strLienD{numDoc}')
                        completName = strLien.split('_')[3]
                        name = docs.create_name(dateDocument, idContrat, id, SType)
                        extention = completName.split('.')[1]
                    LienDocument = name + extention
                    document.strLien = LienDocument

                    # création d'un nom de document
                    date_date = datetime.datetime.strptime(dateDocument, '%Y-%m-%d').date()
                    str_date = date_date.strftime('%y%m%d')
                    str_idContrat = str(idContrat).zfill(6)
                    str_idDocument = str(id).zfill(6)
                    str_SType = SType[:5]
                    name = f"{str_date}_{str_idContrat}_{str_idDocument}_{str_SType}"

                    #Gestion automatique du nom de document
                    document.name = name

                    #Retour
                    g.db_session.commit()

                    return redirect(url_for('contrats_by_num', numContrat = idContrat))
            except Exception as e:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat = numContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/numContrat/<numContrat>/numDocument/<numDoc>/download/<name>', methods=['GET'])
def download_document(numDoc, numContrat, name:str):
    if '2' in str(session['habilitation']):
        extention = name.split('.')[1]
        name = name.split('.')[0]
        return docs.download_file(file_name=name, extension=extention)
    else:
        return redirect(url_for('logout'))
