from flask import Flask, jsonify, render_template, Request, request, redirect, url_for, session, g
from flask.typing import ResponseReturnValue
from werkzeug import Response
from config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from models import Base
import docs
from models import User, Contract, Event, Document
from typing import List, Dict, Any, cast, Optional, Tuple
import hashlib
import datetime
import os
from datetime import timedelta

peraudiere = Flask(__name__)

# Charger la configuration depuis config.py
peraudiere.config.from_object(Config)

# Construction de l'URL de la base de données
db_user: str = cast(str, peraudiere.config["DB_USER"])
db_password: str = cast(str, peraudiere.config["DB_PASSWORD"])
db_host: str = cast(str, peraudiere.config["DB_HOST"])
db_name: str = cast(str, peraudiere.config["DB_NAME"])
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

# Créer les tables de la base de données (avec retry en cas d'erreur de connexion)
def initialize_database():
    import time
    max_retries = 10
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(engine)
            print(f"✓ Base de données initialisée avec succès (tentative {attempt + 1})")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"✗ Tentative {attempt + 1} échouée: {e}")
                print(f"  Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
            else:
                print(f"✗ Échec de la connexion à la base de données après {max_retries} tentatives: {e}")
                raise

# Créer une session de base de données
Session = sessionmaker(bind=engine)

# Création des constantes
UPLOAD_EXTENSIONS = ['.jpg', '.png', '.gif', '.jpeg', '.tif', '.tiff', '.pdf']
RESERVED_SPACE = 'Espace réservé'

# Configuration de l'application
peraudiere.config['UPLOAD_EXTENSIONS'] = UPLOAD_EXTENSIONS
peraudiere.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Initialiser la base de données avec retry
initialize_database()

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


@peraudiere.before_request
def before_request() -> None:
    g.db_session = Session()

@peraudiere.teardown_appcontext
def teardown_request(exception: Optional[BaseException]):
    db_session = g.pop('db_session', None)
    if db_session is not None:
        if exception:
            db_session.rollback()
        db_session.close()

@peraudiere.route('/')
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

@peraudiere.route('/login', methods=['GET', 'POST'])
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

@peraudiere.route('/logout')
def logout() -> Response:
    session.clear()
    return redirect(url_for('login'))

@peraudiere.route('/gestion_droits')
def gestion_droits() -> str | Response:
    if '1' in str(session['habilitation']): 
        users = g.db_session.query(User).all()
        return render_template('gestion_droits.html', users=users)
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/gestion_utilisateurs')
def gestion_utilisateurs() -> str | Response:
    if '2' in str(session['habilitation']): 
        users: list[User] = g.db_session.query(User).all()
        users.sort(key=lambda x: (x.nom, x.prenom))
        return render_template('gestion_utilisateurs.html', users=users)
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/gestion_documents')
def gestion_documents() -> str | Response:
    if '2' in str(session['habilitation']):
        return render_template('gestion_documents.html')
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/erpp')
def erpp() -> str | Response:
    if '3' in str(session['habilitation']):
        return render_template('erpp.html')
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/erp')
def erp() -> str | Response:
    if '4' in str(session['habilitation']): 
        return render_template('erp.html')
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/ei')
def ei() -> str | Response:
    if '6' in str(session['habilitation']):
        return render_template('ei.html')
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/print_doc', methods=['POST'])
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

@peraudiere.route('/ere')
def ere() -> str | Response:
    if '5' in str(session['habilitation']):
        return render_template('ere.html')
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/ajout_utilisateurs', methods=['POST'])
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

@peraudiere.route('/suppr_utilisateurs', methods=['POST'])
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

@peraudiere.route('/modif_utilisateurs', methods=['POST'])
def modif_utilisateurs() -> Response:
    if '1' in str(session['habilitation']) or '2' in str(session['habilitation']): 
        try:
            prenom = request.form.get('prenom', '')
            nom = request.form.get('nom', '')
            mail = request.form.get('mail', '')
            identifiant = request.form.get('identifiant', '')
            mdp = request.form.get('mdp', '')
            mdp = hashlib.sha256(mdp.encode()).hexdigest()
            unlock = int(request.form.get('unlock', 0)) if request.form.get('unlock') == '1' else 0

            #Création du niveau d'habilitation
            habilitation_values: List[str] = []
            habilitation_values.extend(value for key, value in request.form.items() if key.startswith('habil'))

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
                user.shaMdp = mdp if mdp != '' else user.shaMdp
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

@peraudiere.route('/gestion_droits', methods=['POST'])
def gestion_droits_post() -> Response:
    if '1' in str(session['habilitation']) or '2' in str(session['habilitation']): 
        try:
            identifiant = request.form.get('identifiant', '')
            mdp = request.form.get('mdp', '')
            mdp = hashlib.sha256(mdp.encode()).hexdigest()
            
            #Création du niveau d'habilitation
            habilitation_values: List[str] = []
            habilitation_values.extend(value for key, value in request.form.items() if key.startswith('habil'))
            
            #Trier les valeurs d'habilitation
            sorted_habil = sorted(habilitation_values, key=int)

            #Concaténation des valeurs d'habilitation
            habilitation = int(''.join(sorted_habil))

            user = g.db_session.query(User).filter(User.identifiant == identifiant).first()
            if user:
                user.shaMdp = mdp if mdp != '' else user.shaMdp
                user.habilitation = habilitation
                g.db_session.commit()

            return redirect(url_for('gestion_droits'))
        except Exception:
            g.db_session.rollback()
            return redirect(url_for('gestion_droits'))
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/contrats', methods=['GET', 'POST'])
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
                contract = Contract(Type = type_contrat,
                                    SType = sous_type_contrat,
                                    entreprise = entreprise,
                                    numContratExterne = num_contrat_externe,
                                    intitule = intitule,
                                    dateDebut = date_debut,
                                    dateFin = date_fin,
                                    dateFinPreavis = date_fin_preavis
                                    ) \
                           if date_fin != '' \
                           else \
                           Contract(Type = type_contrat,
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

@peraudiere.route('/contrats/<int:numContrat>', methods=['GET', 'POST'])
def contrats_by_num(numContrat: int) -> ResponseReturnValue:
    # alias pour conserver le style snake_case utilisé dans la suite du code
    num_contrat = numContrat
    if request.method == 'GET': 
        contract = g.db_session.query(Contract).filter(Contract.id == num_contrat).first()
        events = g.db_session.query(Event).filter(Event.idContrat == num_contrat)
        documents = g.db_session.query(Document).filter(Document.idContrat == num_contrat)

        return render_template('contrat_detail.html', contract = contract, events = events, documents = documents)
    elif request.method == 'POST' and request.form.get('_method') == 'PUT':
        try:
            contract = g.db_session.query(Contract).filter(Contract.id == num_contrat).first()
            if contract:
                contract.Type = request.form.get(f'Type{num_contrat}')
                contract.SType = request.form.get(f'SType{num_contrat}')
                contract.Entreprise = request.form.get(f'Entreprise{num_contrat}')
                contract.numContratExterne = request.form.get(f'numContratExterne{num_contrat}')
                contract.Intitule = request.form.get(f'Intitule{num_contrat}')
                contract.dateDebut = request.form.get(f'dateDebut{num_contrat}')
                contract.dateFinPreavis = request.form.get(f'dateFinPreavis{num_contrat}')
                if request.form.get(f'dateFin{num_contrat}') != '':
                    contract.dateFin = request.form.get(f'dateFin{num_contrat}')
            
                g.db_session.commit()

            return redirect(url_for('contrats'))
        except Exception:
            g.db_session.rollback()
            return redirect(url_for('contrats'))
    else:
        return redirect(url_for('contrats'))

@peraudiere.route('/contrats/<numContrat>/evenement', methods=['POST'])
def add_contrats_event(numContrat: int) -> ResponseReturnValue:
    num_contrat = numContrat
    if '2' in str(session['habilitation']):
        if request.method == 'POST':
            try:
                #Récupération des données du formulaire*
                id_contrat = request.form.get('idContratE')
                date_evenement = request.form.get('dateEvenementE')
                type_contrat = request.form.get('TypeE0')
                stype_contrat = request.form.get('STypeE0')
                descriptif = request.form.get('descriptifE')

                event = Event(idContrat = id_contrat, dateEvenement = date_evenement, Type = type_contrat, SType = stype_contrat, descriptif = descriptif)
                
                g.db_session.add(event)
                g.db_session.commit()

                return redirect(url_for('contrats_by_num', numContrat=id_contrat))
            except Exception:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat=num_contrat))
        else:
            return redirect(url_for('contrats_by_num', numContrat=num_contrat))
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/contrats/<numContrat>/document', methods=['POST'])
def add_contrats_document(numContrat: int) -> ResponseReturnValue:
    num_contrat = numContrat
    if '2' in str(session['habilitation']):
        if request.method == 'POST':
            try:
                #Récupération du dernier élément
                last_doc = g.db_session.query(Document).order_by(Document.id.desc()).first()
                if last_doc:
                    id_contrat = str(last_doc.id + 1)
                else:
                    id_contrat = '1'

                #Récupération des données du formulaire
                id_contrat = request.form.get('idContratD', '')
                date_document = request.form.get('dateDocumentD', '')
                type_document = request.form.get('TypeD0', '')
                sous_type_document = request.form.get('STypeD0', '')
                descriptif = request.form.get('descriptifD', '')
                document_binaire: Any = request.files['documentD']
                extention: str = os.path.splitext(str(document_binaire.filename))[1]
                name = docs.create_name(date_document, id_contrat, id_contrat, sous_type_document)
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
                return redirect(url_for('contrats_by_num', numContrat=num_contrat))
        else:
            return redirect(url_for('contrats_by_num', numContrat=num_contrat))
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/contrats/numContrat/<numContrat>/numEvenement/<numEvent>', methods=['POST'])
def modif_event_id(numEvent: int, numContrat: int) -> ResponseReturnValue:
    num_event = numEvent
    num_contrat = numContrat
    if '2' in str(session['habilitation']):
        if request.method == 'POST' and request.form.get('_method') == 'PUT':
            try:
                #Récupération de l'évènement
                event = g.db_session.query(Event).filter(Event.id == num_event).first()

                if event:
                    #Récupération formulaire
                    id_contrat = request.form.get(f'idContratE{num_event}')
                    event.idContrat = request.form.get(f'idContratE{num_event}')
                    event.dateEvenement = request.form.get(f'dateEvenementE{num_event}')
                    event.Type = request.form.get(f'TypeE{num_event}')
                    event.SType = request.form.get(f'STypeE{num_event}')
                    event.descriptif = request.form.get(f'descriptifE{num_event}')

                    #Retour
                    g.db_session.commit()

                    return redirect(url_for('contrats_by_num', numContrat = id_contrat))
                else:
                    return redirect(url_for('contrats_by_num', numContrat = num_contrat))
            except Exception:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat = num_contrat))
        else:
            return redirect(url_for('contrats_by_num', numContrat = num_contrat))
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/contrats/numContrat/<numContrat>/numDocument/<numDoc>', methods=['POST'])
def modif_document_id(numDoc: int, numContrat: int) -> ResponseReturnValue:
    num_doc = numDoc
    num_contrat = numContrat

    def _fonction_modif_doc(document: Document, req: Request, num_doc: int) -> int:
        doc_id = document.id
        id_contrat = req.form.get(f'idContratD{num_doc}', '')
        date_document = req.form.get(f'dateDocumentD{num_doc}', '')
        document.dateDocument = date_document
        type_document = req.form.get(f'TypeD{num_doc}', '')
        document.Type = type_document
        stype_document = req.form.get(f'STypeD{num_doc}', '')
        document.SType = stype_document
        document.descriptif = req.form.get(f'descriptifD{num_doc}', '')
        if req.files[f'documentD{num_doc}']:
            document_binaire = req.files[f'documentD{num_doc}']
            name = docs.create_name(date_document, id_contrat, doc_id, stype_document)
            extention = os.path.splitext(str(document_binaire.filename))[1]
        else:
            str_lien = req.form.get(f'strLienD{num_doc}', '')
            complet_name = str_lien.split('_')[3]
            name = docs.create_name(date_document, id_contrat, doc_id, stype_document)
            extention = complet_name.split('.')[1]
        lien_document = name + extention
        document.strLien = lien_document

        # création d'un nom de document
        date_date = datetime.datetime.strptime(date_document, '%Y-%m-%d').date()
        str_date = date_date.strftime('%y%m%d')
        str_id_contrat = str(id_contrat).zfill(6)
        str_id_document = str(doc_id).zfill(6)
        str_stype = stype_document[:5]
        name = f"{str_date}_{str_id_contrat}_{str_id_document}_{str_stype}"

        #Gestion automatique du nom de document
        document.name = name

        #Retour
        g.db_session.commit()

        return document.id

    if '2' in str(session['habilitation']):
        if request.method == 'POST' and request.form.get('_method') == 'PUT':
            try:
                #Récupération du document
                document = g.db_session.query(Document).filter(Document.id == num_doc).first()

                # Création du document et récupération de son id
                id_contrat = _fonction_modif_doc(document, request, num_doc)
                return redirect(url_for('contrats_by_num', numContrat = id_contrat))

            except Exception:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat = num_contrat))
        else:
            return redirect(url_for('contrats_by_num', numContrat = num_contrat))
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/contrats/numContrat/<numContrat>/numDocument/<numDoc>/download/<name>', methods=['GET'])
def download_document(numDoc: int, numContrat: int, name: str):
    if '2' in str(session['habilitation']):
        extention = name.split('.')[1]
        name = name.split('.')[0]
        return docs.download_file(file_name=name, extension=extention)
    else:
        return redirect(url_for('logout'))

@peraudiere.route('/rapport-contrats', methods=['POST'])
def rapport_contrats() -> Response:
    email: str = request.args.get('email', '')
    try:
        from rapport_echeances import envoi_contrats_renego
        envoi_contrats_renego(email)
        return jsonify(f"Rapport envoyé à {email}", 200)
    except Exception as e:
        return jsonify(f"Erreur lors de l'envoi du rapport à {email} : {e}", 500)