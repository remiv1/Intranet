"""
==================================================
Application principale de l'Intranet API'Raudière
==================================================
Fichier de l'application principale de l'Intranet API'Raudière.

Auteur : Rémi Verschuur

Date : 2025-09-11

Routes disponibles :
- '/' : Page d'accueil
- '/login' : Page de connexion
- '/logout' : Déconnexion de l'utilisateur
- '/gestion-droits' [GET] : Gestion des droits des utilisateurs
- '/gestion-droits' [POST] : Modification des droits d'un utilisateur
- '/gestion-utilisateurs' [GET] : Gestion des utilisateurs
- '/gestion-documents' [GET] : Gestion des documents
- '/erpp' [GET] : Espace réservé pour les professeurs principaux
- '/erp' [GET] : Espace réservé pour les professeurs
- '/ei' [GET] : Espace impressions
- '/print-doc' [POST] : Impression d'un document
- '/ere' [GET] : Espace réservé pour les élèves
- '/ajout-utilisateurs' [POST] : Ajout d'un utilisateur
- '/suppr-utilisateurs' [POST] : Suppression d'un utilisateur
- '/modif-utilisateurs' [POST] : Modification d'un utilisateur
- '/rapport-contrats' [POST] : Rapport des contrats arrivant à échéance entre m-6 et m-3
"""
# Imports liés à Flask et SQLAlchemy
from flask import Flask, jsonify, render_template, Request, request, redirect, url_for, session, g
from flask.wrappers import Response
from werkzeug import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

# Imports liés à l'application
from habilitations import (validate_habilitation, ADMINISTRATEUR, GESTIONNAIRE, PROFESSEURS_PRINCIPAUX,
                           PROFESSEURS, ELEVES, IMPRESSIONS)
from bp_contracts import contracts_bp
from config import Config
from models import Base, User
from docs import print_document, delete_file
from rapport_echeances import envoi_contrats_renego
from utilities import get_jsoned_datas

# Imports standards
from typing import List, Dict, Any, cast, Optional, Tuple
from hashlib import sha256
from os.path import splitext
import logging
from datetime import datetime

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler("application.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("peraudiere")

# Initialisation de l'application Flask
peraudiere = Flask(__name__)

# Enregistrement du blueprint pour les contrats
peraudiere.register_blueprint(contracts_bp)

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
                        echo=False)

# Créer les tables de la base de données (avec retry en cas d'erreur de connexion)
def initialize_database(max_retries: int = 10, retry_delay: int = 2) -> bool | None:
    import time
    
    # Tenter de créer les tables avec des retries
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(engine)
            return True
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

# Créer une session de base de données sans ouverture de celle-ci
Session = sessionmaker(bind=engine)

# Initialiser la base de données avec retry
initialize_database()

class UsersMethods:
    """
    Classe pour gérer les méthodes liées aux utilisateurs.
    Méthodes statiques :
    - get_user_from_credentials : Récupère un utilisateur à partir des identifiants fournis dans une requête.
    - valid_authentication : Valide l'authentification d'un utilisateur et initialise la session.
    - generate_nb_false_pwd : Gère le compteur d'essais de mot de passe incorrects et verrouille l'utilisateur si nécessaire.
    """
    
    @staticmethod
    def get_user_from_credentials(request: Request) -> Tuple[User, str, str]:
        """
        Récupère un utilisateur à partir des identifiants fournis dans une requête.
        Args:
            request (Request): La requête contenant les identifiants :
                - 'username' : nom d'utilisateur
                - 'password' : mot de passe
        Returns:
            Tuple[User, str, str]: Un tuple contenant l'utilisateur, le nom d'utilisateur et le mot de passe.
        """
        # Récupération du credential
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        password = sha256(password.encode()).hexdigest()

        try:
            # Recherche de l'utilisateur dans la base de données
            user = g.db_session.query(User).filter(User.identifiant == username).first()

        except Exception:
            # Gérer les exceptions potentielles
            user = User()

        # Retourne les identifiants de l'utilisateur et l'utilisateur
        return user, username, password

    @staticmethod
    def valid_authentication(user: User, password: str) -> bool:
        """
        Valide l'authentification d'un utilisateur et initialise la session.
        Args:
            user (User): L'utilisateur à valider.
            password (str): Le mot de passe fourni pour la validation.
        Returns:
            bool: True si l'authentification est réussie, False sinon.
        """
        if user.locked:
            return False
        elif user.fin:
            if user.fin <= datetime.now():
                return False
        elif user and user.sha_mdp == password:
            session['identifiant'] = user.identifiant
            session['prenom'] = user.prenom
            session['nom'] = user.nom
            session['mail'] = user.mail
            session['habilitation'] = str(user.habilitation)
            try:
                # Stocker les informations de l'utilisateur dans la session
                user.false_test=0
                g.db_session.commit()
                return True
            except Exception:
                return False
        return False

    @staticmethod
    def generate_nb_false_pwd(user: User) -> str:
        """
        Gère le compteur d'essais de mot de passe incorrects et verrouille l'utilisateur si nécessaire.
        Args:
            user (User): L'utilisateur pour lequel gérer le compteur d'essais.
        Returns:
            str: Un message indiquant le résultat de l'opération.
        """
        if user.false_test < 2:
            user.false_test += 1
            reste = 3 - user.false_test
            message = f'Erreur d\'identifiant ou de mot de passe, il vous reste {reste} essais.'
        else:
            user.locked = True
            user.false_test = 3
            message = f'Utilisateur {user.nom} vérouillé, merci de contacter votre administrateur.'
        try:
            g.db_session.commit()
        except Exception as e:
            message = f'Erreur lors de la mise à jour du compteur d\'essais : {e}'
        return message

@peraudiere.before_request
def before_request() -> Any:
    """
    Fonction exécutée avant chaque requête.
    Initialise une session de base de données et la stocke dans l'objet `g`.
    Args:
        None
    Returns:
        None
    """
    if 'db_session' not in g:
        g.db_session = Session()
    # Autoriser l'accès aux fichiers CSS et autres fichiers statiques
    match request.endpoint:
        case 'rapport_contrats':
            api_token = request.headers.get('X-API-TOKEN')
            if api_token and api_token == peraudiere.config['API_MAIL_TOKEN']:
                return None
        case 'static':
            return None
        case 'login':
            return None
        case 'logout':
            return None
        case _:
            if 'prenom' not in session or 'nom' not in session:
                session.clear()
                error_message = 'Merci de vous connecter pour accéder à cette ressource'
                return redirect(url_for('login', error_message=error_message))

@peraudiere.teardown_appcontext
def teardown_request(exception: Optional[BaseException]) -> None:
    """
    Fonction exécutée après chaque requête.
    Ferme la session de base de données stockée dans l'objet `g` et réalise les rollbacks si nécessaire.
    Args:
        exception (Optional[BaseException]): Une exception éventuelle survenue lors de la requête.
    Returns:
        None
    """
    db_session = g.pop('db_session', None)
    if db_session is not None:
        db_session.rollback()
        db_session.close()

@peraudiere.route('/')
def home() -> str | Response:
    """
    Route pour la page d'accueil.
    Si l'utilisateur est connecté, affiche la page d'accueil avec les informations utilisateur et les sections disponibles.
    Sinon, redirige vers la page de connexion.
    Args:
        None
    Returns:
        str | Response: La page d'accueil ou une redirection vers la page de connexion.
    """
    # Récupération des messages passés en paramètres GET
    message = request.args.get('message', None)
    success_message = request.args.get('success_message', None)
    error_message = request.args.get('error_message', None)

    # Validation de l'existence de la session utilisateur avec les éléments nécessaires
    if 'prenom' in session and 'nom' in session:
        prenom = session['prenom']
        nom = session['nom']
        habilitation = session['habilitation']
        
        # création d'une liste de niveaux d'habilitation
        habilitation_levels = list(map(int, str(habilitation)))

        # définition des sections disponibles en fonction des habilitations
        sections: List[Dict[str, Any]] = get_jsoned_datas(file='modules.json', level_one='modules', dumped=False)

        # Retourne la page d'accueil avec les informations utilisateur et les sections disponibles
        return render_template('index.html', prenom=prenom, nom=nom, habilitation_levels=habilitation_levels,
                               sections=sections, message=message, success_message=success_message,
                               error_message=error_message)
    else:
        error_message = 'Merci de vous connecter pour accéder à cette ressource'
        return redirect(url_for('login', error_message=error_message))

@peraudiere.route('/login', methods=['GET', 'POST'])
def login() -> str | Response:
    """
    Route pour la page de connexion.
    Gère l'affichage du formulaire de connexion et le traitement des informations de connexion.
    Args:
        None
    Returns:
        Response | str: La page de connexion ou une redirection vers la page d'accueil.
    """
    # Récupération des messages passés en paramètres GET
    message = request.args.get('message', None)
    success_message = request.args.get('success_message', None)
    error_message = request.args.get('error_message', None)

    # === Gestion de la méthode POST (traitement du formulaire de connexion) ===
    if request.method == 'POST':
        try:
            # récupération du contenu du formulaire
            user, _, password = UsersMethods.get_user_from_credentials(request)

            # Vérifier si l'utilisateur existe et si le mot de passe est correct
            if UsersMethods.valid_authentication(user, password):
                return redirect(url_for('home', success_message='Connexion réussie'))
            # Gestion des comptes vérouillés
            elif user.fin:
                if user.fin <= datetime.now():
                    message = 'Votre compte a expiré, veuillez contacter votre administrateur.'
            elif user.locked:
                message = 'Votre compte est verrouillé, veuillez contacter votre administrateur.'
            # Gestion des erreurs de mots de passe
            else:
                message = UsersMethods.generate_nb_false_pwd(user)

            # Rediriger vers la page de connexion avec le message approprié
            return redirect(url_for('login', error_message=message))

        except Exception as e:
            # En cas d'erreur, retour sur la page de connexion après rollback
            message = f'Erreur lors de la connexion, veuillez réessayer : {e}'
            return redirect(url_for('login', error_message=message))

    # === Gestion de la méthode GET (affichage de la page de connexion) ===
    else:
        return render_template('login.html', message=message, success_message=success_message,
                               error_message=error_message)

@peraudiere.route('/logout', methods=['GET'])
def logout() -> Response:
    """
    Route pour la déconnexion de l'utilisateur.
    Gère la suppression de la session utilisateur.
    Args:
        None
    Returns:
        Response: Redirection vers la page de connexion.
    """
    success_message = request.args.get('success_message', None)
    error_message = request.args.get('error_message', None)
    session.clear()
    return redirect(url_for('login', message='Vous avez été déconnecté', success_message=success_message,
                            error_message=error_message))

@peraudiere.route('/gestion-droits', methods=['GET'])
@validate_habilitation(ADMINISTRATEUR)
def gestion_droits() -> str | Response:
    """
    Route pour la gestion des droits des utilisateurs.
    Gère l'affichage et la modification des droits des utilisateurs.
    Args:
        None
    Returns:
        Response: La page de gestion des droits ou une redirection vers la page de déconnexion.
    """
    message = request.args.get('message', None)
    success_message = request.args.get('success_message', None)
    error_message = request.args.get('error_message', None)
    users = g.db_session.query(User).all()
    return render_template('gestion_droits.html', users=users, message=message,
                           success_message=success_message, error_message=error_message)

@peraudiere.route('/gestion-utilisateurs', methods=['GET'])
@validate_habilitation(GESTIONNAIRE)
def gestion_utilisateurs(message: Optional[str] = None, success_message: Optional[str] = None,
                         error_message: Optional[str] = None) -> str | Response:
    """
    Route pour la gestion des utilisateurs.
    Gère l'affichage et la modification des utilisateurs.
    Args:
        None
    Returns:
        Response: La page de gestion des utilisateurs ou une redirection vers la page de déconnexion.
    """
    users: list[User] = g.db_session.query(User).all()
    users.sort(key=lambda x: (x.nom, x.prenom))
    return render_template('gestion_utilisateurs.html', users=users, message=message,
                           success_message=success_message, error_message=error_message)

@peraudiere.route('/erpp')
@validate_habilitation(PROFESSEURS_PRINCIPAUX)
def erpp(message: Optional[str] = None, success_message: Optional[str] = None,
          error_message: Optional[str] = None) -> str | Response:
    """
    Route pour l'espace réservé aux professeurs principaux.
    Gère l'affichage de l'espace réservé aux professeurs principaux.
    Args:
        None
    Returns:
        Response: La page de l'espace réservé aux professeurs principaux.
    """
    return render_template('erpp.html', message=message, success_message=success_message,
                           error_message=error_message)

@peraudiere.route('/erp')
@validate_habilitation(PROFESSEURS)
def erp(message: Optional[str] = None, success_message: Optional[str] = None,
         error_message: Optional[str] = None) -> str | Response:
    """
    Route pour l'espace réservé aux professeurs.
    Gère l'affichage de l'espace réservé aux professeurs.
    Args:
        None
    Returns:
        Response: La page de l'espace réservé aux professeurs.
    """
    return render_template('erp.html', message=message, success_message=success_message,
                           error_message=error_message)

@peraudiere.route('/ei')
@validate_habilitation(IMPRESSIONS)
def ei(message: Optional[str] = None, success_message: Optional[str] = None,
        error_message: Optional[str] = None) -> str | Response:
    """
    Route pour l'espace réservé aux impressions.
    Gère l'affichage de l'espace réservé aux impressions.
    Args:
        None
    Returns:
        Response: La page de l'espace réservé aux impressions.
    """
    return render_template('ei.html', message=message, success_message=success_message,
                           error_message=error_message)

@peraudiere.route('/print-doc', methods=['POST'])
@validate_habilitation(IMPRESSIONS)
def print_doc() -> Response:
    """
    Route pour l'impression d'un document.
    Gère l'impression d'un document via SSH.
    Args:
        None
    Returns:
        Response: Redirection vers la page de l'espace réservé aux
                  impressions avec un message de succès.
    """
    try:
        binary_document: Any = request.files['document']
        document = str(binary_document.filename)
        extension: str = str(splitext(document))[1]
        docname = document.split('.')[0]
        username = session['prenom'] + ' ' + session['nom']
        copies: str = str(request.form.get('copies'))
        sides: str = request.form.get('recto_verso', '')
        media: str = request.form.get('format', '')
        orientation: str = request.form.get('orientation', '')
        color: str = request.form.get('couleur', '')

        # Envoi du document à l'imprimante
        print_document(binary_document,docname, extension, copies, username, sides, media, orientation, color)

        # Suppression du document sur le serveur
        delete_file(docname, extension)

        return redirect(url_for('ei', success_message='Impression envoyée'))
    except Exception:
        return redirect(url_for('ei', error_message='Erreur lors de l\'impression, veuillez réessayer'))

@peraudiere.route('/ere')
@validate_habilitation(ELEVES)
def ere(message: Optional[str] = None, success_message: Optional[str] = None,
         error_message: Optional[str] = None) -> str | Response:
    """
    Route pour l'espace réservé aux élèves.
    Gère l'affichage de l'espace réservé aux élèves.
    Args:
        None
    Returns:
        Response: La page de l'espace réservé aux élèves.
    """
    return render_template('ere.html', message=message, success_message=success_message,
                           error_message=error_message)

@peraudiere.route('/ajout-utilisateurs', methods=['POST'])
@validate_habilitation(ADMINISTRATEUR)
def ajout_utilisateurs() -> Response:
    """
    Route pour l'ajout d'un utilisateur.
    Gère l'ajout d'un utilisateur à la base de données.
    Args:
        None
    Returns:
        Response: Redirection vers la page de gestion des utilisateurs.
    """
    try:
        # Récupération des données du formulaire
        prenom = request.form.get('prenom')
        nom = request.form.get('nom')
        mail = request.form.get('mail')
        identifiant = request.form.get('identifiant')
        mdp = request.form.get('mdp', '')
        mdp = sha256(mdp.encode()).hexdigest()

        # Création du niveau d'habilitation
        habilitation_values: List[str] = []
        for key, value in request.form.items():
            if key.startswith('habil'):
                habilitation_values.append(value)
    
        # Trier les valeurs d'habilitation
        sorted_habil = sorted(habilitation_values, key=int)

        # Concaténation des valeurs d'habilitation
        habilitation = int(''.join(sorted_habil))

        user = User(prenom=prenom, nom=nom,
                    identifiant=identifiant,
                    mail=mail, habilitation=habilitation,
                    sha_mdp=mdp)
        g.db_session.add(user)
        g.db_session.commit()

        message = f'Utilisateur {identifiant} ajouté avec succès'
        return redirect(url_for('gestion_utilisateurs', success_message=message))
    except Exception as e:
        message = f'Erreur lors de l\'ajout de l\'utilisateur : {e}'
        return redirect(url_for('gestion_utilisateurs', error_message=message))

@peraudiere.route('/suppr-utilisateurs', methods=['POST'])
@validate_habilitation(ADMINISTRATEUR)
def suppr_utilisateurs() -> Response:
    """
    Route pour la suppression d'un utilisateur.
    Gère la suppression d'un utilisateur de la base de données.
    Args:
        None
    Returns:
        Response: Redirection vers la page de gestion des utilisateurs.
    """
    identifiant = request.form.get('identifiant', '')
    try:
        user = g.db_session.query(User).filter(User.identifiant == identifiant).first()
        if user:
            g.db_session.delete(user)
            g.db_session.commit()
        message = f'Utilisateur {identifiant} supprimé avec succès'
        return redirect(url_for('gestion_utilisateurs', success_message=message))
    except Exception as e:
        message = f'Erreur lors de la suppression de l\'utilisateur {identifiant} : {e}'
        return redirect(url_for('gestion_utilisateurs', error_message=message))

@peraudiere.route('/modif-utilisateurs', methods=['POST'])
@validate_habilitation(ADMINISTRATEUR)
def modif_utilisateurs() -> Response:
    """
    Route pour la modification d'un utilisateur.
    Gère la modification d'un utilisateur dans la base de données.
    Args:
        None
    Returns:
        Response: Redirection vers la page de gestion des utilisateurs.
    """
    prenom = request.form.get('prenom', '')
    nom = request.form.get('nom', '')
    mail = request.form.get('mail', '')
    identifiant = request.form.get('identifiant', '')
    mdp = request.form.get('mdp', '')
    unlock = int(request.form.get('unlock', 0)) if request.form.get('unlock') == '1' else 0
    try:
        # Hachage du mot de passe
        mdp = sha256(mdp.encode()).hexdigest()

        # Création du niveau d'habilitation
        habilitation_values: List[str] = []
        habilitation_values.extend(value for key, value in request.form.items() if key.startswith('habil'))
        sorted_habil = sorted(habilitation_values, key=int)     # Trier les valeurs d'habilitation
        habilitation = int(''.join(sorted_habil))               # Concaténation des valeurs d'habilitation

        # Récupération de l'utilisateur
        user = g.db_session.query(User).filter(User.identifiant == identifiant).first()

        # Modification des informations de l'utilisateur
        if user:
            user.prenom = prenom
            user.nom = nom
            user.mail = mail
            user.identifiant = identifiant
            user.sha_mdp = mdp if mdp != '' else user.sha_mdp
            if unlock == 1:
                user.false_test = 0
                user.locked = False
            user.habilitation = habilitation

            # Commit des modifications
            g.db_session.commit()

        # Message de succès et redirection
        message = f'Utilisateur {identifiant} modifié avec succès'
        return redirect(url_for('gestion_utilisateurs', success_message=message))
    except Exception as e:
        # Message d'erreur et redirection
        message = f'Erreur lors de la modification de l\'utilisateur {identifiant} : {e}'
        return redirect(url_for('gestion_utilisateurs', error_message=message))

@peraudiere.route('/gestion-droits', methods=['POST'])
@validate_habilitation([ADMINISTRATEUR, GESTIONNAIRE])
def gestion_droits_post() -> Response:
    """
    Route pour la gestion des droits d'un utilisateur.
    Gère la modification des droits d'un utilisateur dans la base de données.
    Args:
        None
    Returns:
        Response: Redirection vers la page de gestion des droits.
    """
    # Récupération des données du formulaire
    identifiant = request.form.get('identifiant', '')
    mdp = request.form.get('mdp', '')

    try:
        # Hachage du mot de passe
        mdp = sha256(mdp.encode()).hexdigest()
        habilitation_values: List[str] = []  # Création du niveau d'habilitation
        habilitation_values.extend(value for key, value in request.form.items() if key.startswith('habil'))
        sorted_habil = sorted(habilitation_values, key=int)     # Tri des valeurs d'habilitation
        habilitation = int(''.join(sorted_habil))               # Concaténation des valeurs d'habilitation

        # Récupération de l'utilisateur
        user = g.db_session.query(User).filter(User.identifiant == identifiant).first()

        # Modification des informations de l'utilisateur
        if user:
            user.sha_mdp = mdp if mdp != '' else user.sha_mdp
            user.habilitation = habilitation
            g.db_session.commit()

        # Message de succès et redirection
        message = f'Droits de l\'utilisateur {identifiant} modifiés avec succès'
        return redirect(url_for('gestion_droits', success_message=message))
    except Exception as e:
        # Message d'erreur et redirection
        message = f'Erreur lors de la modification des droits de l\'utilisateur {identifiant} : {e}'
        return redirect(url_for('gestion_droits', error_message=message))

@peraudiere.route('/rapport-contrats', methods=['POST'])
def rapport_contrats() -> Response:
    """
    Route pour l'envoi du rapport des contrats à renégocier.
    Gère l'envoi du rapport des contrats à renégocier par email.
    Args:
        None
    Returns:
        Response: Un message JSON indiquant le résultat de l'opération.
    """
    email: str = request.args.get('email', '')
    try:
        envoi_contrats_renego(email)
        return jsonify(f"Rapport envoye a {email}", 200)
    except Exception as e:
        return jsonify(f"Erreur lors de l envoi du rapport a {email} : {e}", 500)
