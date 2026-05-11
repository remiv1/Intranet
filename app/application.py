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
# Imports standards
from typing import List, Dict, Any, Optional
from hashlib import sha256
from os.path import splitext
from datetime import datetime

# Imports liés à Flask et SQLAlchemy
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, g
from flask.wrappers import Response
from werkzeug import Response as WResponse
from sqlalchemy.exc import SQLAlchemyError

# Imports liés à l'application
from .habilitations import (
    validate_habilitation,
    ADMINISTRATEUR,
    GESTIONNAIRE,
    PROFESSEURS_PRINCIPAUX,
    PROFESSEURS,
    ELEVES,
    IMPRESSIONS,
    VPN
)
from .bp_contracts import contracts_bp
from .bp_signature import signatures_bp
from .config.config import ConfigApp
from .models import User, DocToSigne, Points, Signatures, Invitation
from app.repositories.user import handle_login_post
from .docs import print_document, delete_file
from .rapport_echeances import envoi_contrats_renego
from .utilities import get_jsoned_datas
from .config.logger import api_logger
from app.config.database import SESSION, initialize_database
# Initialisation de l'application Flask
peraudiere = Flask(__name__)

BLUEPRINTS = [contracts_bp, signatures_bp]
# Enregistrement des blueprints
for bp in BLUEPRINTS:
    peraudiere.register_blueprint(bp)

# Charger la configuration depuis la configuration de l'application
peraudiere.config.from_object(ConfigApp)

# Initialiser la base de données avec retry
initialize_database()


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
    api_logger.info(f"Requête entrante : {request.method} {request.path}")
    if 'db_session' not in g:
        g.db_session = SESSION()
    # Autoriser l'accès aux fichiers CSS et autres fichiers statiques
    match request.endpoint:
        case 'rapport_contrats':
            api_token = request.headers.get('X-API-TOKEN')
            if api_token and api_token == ConfigApp.SECRET_KEY:
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
                # Capturer l'URL complète pour la redirection après connexion (uniquement en GET)
                preview_request = request.url if request.method == 'GET' else None
                return redirect(url_for(
                    'login',
                    error_message=error_message,
                    preview_request=preview_request
                    ))


@peraudiere.teardown_appcontext
def teardown_request(exception: Optional[BaseException]) -> None:
    """
    Fonction exécutée après chaque requête.
    Ferme la session de base de données stockée dans l'objet `g` et réalise
    les rollbacks si nécessaire.
    Args:
        exception (Optional[BaseException]): Une exception éventuelle survenue lors de la requête.
    Returns:
        None
    """
    db_session = g.pop('db_session', None)
    if db_session is not None:
        db_session.rollback()
        db_session.close()
    if exception:
        api_logger.error(f"Exception lors de la requête : {exception}")


@peraudiere.get('/')
def home() -> str | Response | WResponse:
    """
    Route pour la page d'accueil.
    Si l'utilisateur est connecté, affiche la page d'accueil avec les informations utilisateur
    et les sections disponibles. Sinon, redirige vers la page de connexion.
    Args:
        None
    Returns:
        str | Response | WResponse: La page d'accueil ou une redirection vers la page de connexion.
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
        sections: List[Dict[str, Any]] = get_jsoned_datas(
            file='modules.json',
            level_one='modules',
            dumped=False)

        # Retourne la page d'accueil avec les informations utilisateur et les sections disponibles
        return render_template(
            'index.html',
            prenom=prenom,
            nom=nom,
            habilitation_levels=habilitation_levels,
            sections=sections,
            message=message,
            success_message=success_message,
            error_message=error_message
            )
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
    preview_request = request.args.get('preview_request', None)

    # === Gestion de la méthode POST (traitement du formulaire de connexion) ===
    if request.method == 'POST':
        return handle_login_post()

    # === Gestion de la méthode GET (affichage de la page de connexion) ===
    return render_template('login.html', message=message, success_message=success_message,
                           error_message=error_message, preview_request=preview_request)


@peraudiere.get('/logout')
def logout() -> Response | WResponse:
    """
    Route pour la déconnexion de l'utilisateur.
    Gère la suppression de la session utilisateur.
    Args:
        None
    Returns:
        Response | WResponse: Redirection vers la page de connexion.
    """
    success_message = request.args.get('success_message', None)
    error_message = request.args.get('error_message', None)
    session.clear()
    return redirect(url_for(
        'login',
        message='Vous avez été déconnecté',
        success_message=success_message,
        error_message=error_message
        ))


@peraudiere.get('/gestion-droits')
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


@peraudiere.get('/gestion-utilisateurs')
@validate_habilitation(GESTIONNAIRE)
def gestion_utilisateurs(message: Optional[str] = None, success_message: Optional[str] = None,
                         error_message: Optional[str] = None) -> str | Response:
    """
    Route pour la gestion des utilisateurs.
    Gère l'affichage et la modification des utilisateurs.
    Args:
        None
    Returns:
        str | Response:
            La page gestion des utilisateurs ou une redirection vers la page de déconnexion.
    """
    message = request.args.get('message', message)
    success_message = request.args.get('success_message', success_message)
    error_message = request.args.get('error_message', error_message)
    users: list[User] = g.db_session.query(User).all()
    users.sort(key=lambda x: (x.nom, x.prenom))
    return render_template('gestion_utilisateurs.html', users=users, message=message,
                           success_message=success_message, error_message=error_message)


@peraudiere.get('/erpp')
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


@peraudiere.get('/erp')
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


@peraudiere.get('/ei')
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


@peraudiere.get('/ea')
@validate_habilitation(GESTIONNAIRE)
def ea(message: Optional[str] = None, success_message: Optional[str] = None,
        error_message: Optional[str] = None, context: Optional[str] = None) -> str | Response:
    """
    Route pour l'espace réservé aux administrateurs.
    Gère l'affichage de l'espace réservé aux administrateurs.
    Args:
        None
    Returns:
        Response: La page de l'espace réservé aux administratifs.
    """
    message = request.args.get('message', message)
    success_message = request.args.get('success_message', success_message)
    error_message = request.args.get('error_message', error_message)
    context = request.args.get('context', context)
    # définition des sections disponibles en fonction des habilitations
    sections: List[Dict[str, Any]] = get_jsoned_datas(
        file='admin_modules.json',
        level_one='modules',
        dumped=False
        )

    return render_template('ea.html', message=message, success_message=success_message,
                           error_message=error_message, sections=sections, context=context)


@peraudiere.route('/print-doc', methods=['POST'])
@validate_habilitation(IMPRESSIONS)
def print_doc() -> Response | WResponse:
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
        docname = document.split('.', maxsplit=1)[0]
        username = session['prenom'] + ' ' + session['nom']
        copies: str = str(request.form.get('copies'))
        sides: str = request.form.get('recto_verso', '')
        media: str = request.form.get('format', '')
        orientation: str = request.form.get('orientation', '')
        color: str = request.form.get('couleur', '')

        # Envoi du document à l'imprimante
        print_document(
            binary_document,
            docname,
            extension,
            copies,
            username,
            sides,
            media,
            orientation,
            color
        )

        # Suppression du document sur le serveur
        delete_file(docname, extension)

        return redirect(url_for('ei', success_message='Impression envoyée'))
    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as e:
        return redirect(url_for(
            'ei',
            error_message=f'Erreur {e} lors de l\'impression, veuillez réessayer'
            ))


@peraudiere.get('/ere')
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


@peraudiere.post('/ajout-utilisateurs')
@validate_habilitation(ADMINISTRATEUR)
def ajout_utilisateurs() -> Response | WResponse:
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

    except (ValueError, SQLAlchemyError) as e:
        message = f'Erreur lors de l\'ajout de l\'utilisateur : {e}'
        return redirect(url_for('gestion_utilisateurs', error_message=message))


@peraudiere.post('/suppr-utilisateurs/<id_user>')
@validate_habilitation(ADMINISTRATEUR)
def suppr_utilisateurs(id_user: int) -> Response | WResponse:
    """
    Route pour la suppression d'un utilisateur.
    Gère la suppression d'un utilisateur de la base de données.
    Args:
        None
    Returns:
        Response: Redirection vers la page de gestion des utilisateurs.
    """
    # Récupération des données du formulaire
    try:
        # Récupération de l'utilisateur
        user = g.db_session.query(User).filter(User.identifiant == id_user).first()
        if user.id == session['id']:
            message = 'Vous ne pouvez pas supprimer votre propre compte utilisateur.'
            return redirect(url_for('gestion_utilisateurs', error_message=message))
        if user:
            # Vérification des liens avec les documents à signer et les signatures
            docs = g.db_session.query(DocToSigne) \
                            .join(Points) \
                            .join(Signatures) \
                            .join(Invitation) \
                            .filter(DocToSigne.id_user == user.id) \
                            .count()

            # Si des liens existent, désactivation du compte au lieu de la suppression
            if docs > 0:
                user.fin = datetime.now()
                g.db_session.commit()
                message = f"L'utilisateur {id_user} ne peut pas être supprimé car il est lié" + \
                            " à des documents ou des signatures. Son compte a été désactivé."
                return redirect(url_for('gestion_utilisateurs', message=message))

            # Sinon, suppression pure et simple de l'utilisateur
            else:
                g.db_session.delete(user)
                g.db_session.commit()
                message = f'Utilisateur {id_user} supprimé avec succès'
                return redirect(url_for('gestion_utilisateurs', success_message=message))

        # Si l'utilisateur n'existe pas (peu possible car le formulaire est généré dynamiquement)
        else:
            message = f'L\'utilisateur {id_user} n\'existe pas'
            return redirect(url_for('gestion_utilisateurs', error_message=message))

    # Gestion des erreurs
    except (ValueError, AttributeError, TypeError) as e:
        message = f'Erreur lors de la suppression de l\'utilisateur {id_user} : {e}'
        return redirect(url_for('gestion_utilisateurs', error_message=message))


@peraudiere.post('/modif-utilisateurs')
@validate_habilitation(ADMINISTRATEUR)
def modif_utilisateurs() -> Response | WResponse:
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
        # Création du niveau d'habilitation
        habilitation_values: List[str] = []
        habilitation_values.extend(
            value for key, value in request.form.items()
            if key.startswith('habil')
            )
        sorted_habil = sorted(habilitation_values, key=int)
        habilitation = int(''.join(sorted_habil))

        # Récupération de l'utilisateur
        user = g.db_session.query(User).filter(User.identifiant == identifiant).first()

        # Modification des informations de l'utilisateur
        if user:
            user.prenom = prenom
            user.nom = nom
            user.mail = mail
            user.identifiant = identifiant
            user.sha_mdp = sha256(mdp.encode()).hexdigest() if len(mdp) > 0 else user.sha_mdp
            if unlock == 1:
                user.false_test = 0
                user.locked = False
            user.habilitation = habilitation

            # Commit des modifications
            g.db_session.commit()

        # Message de succès et redirection
        message = f'Utilisateur {identifiant} modifié avec succès'
        return redirect(url_for('gestion_utilisateurs', success_message=message))
    except (ValueError, AttributeError, TypeError) as e:
        # Message d'erreur et redirection
        message = f'Erreur lors de la modification de l\'utilisateur {identifiant} : {e}'
        return redirect(url_for('gestion_utilisateurs', error_message=message))


@peraudiere.post('/gestion-droits')
@validate_habilitation([ADMINISTRATEUR, GESTIONNAIRE])
def gestion_droits_post() -> Response | WResponse:
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
        habilitation_values: List[str] = []  # Création du niveau d'habilitation
        habilitation_values.extend(
            value for key, value in request.form.items()
            if key.startswith('habil')
            )
        sorted_habil = sorted(habilitation_values, key=int)
        habilitation = int(''.join(sorted_habil))

        # Récupération de l'utilisateur
        user = g.db_session.query(User).filter(User.identifiant == identifiant).first()

        # Modification des informations de l'utilisateur
        if user:
            user.sha_mdp = sha256(mdp.encode()).hexdigest() if len(mdp) > 0 else user.sha_mdp
            user.habilitation = habilitation
            g.db_session.commit()

        # Message de succès et redirection
        message = f'Droits de l\'utilisateur {identifiant} modifiés avec succès'
        return redirect(url_for('gestion_droits', success_message=message))

    except (ValueError, AttributeError, TypeError) as e:
        # Message d'erreur et redirection
        message = f'Erreur lors de la modification des droits de l\'utilisateur {identifiant} : {e}'
        return redirect(url_for('gestion_droits', error_message=message))


@peraudiere.get('/vpn')
@validate_habilitation(VPN)
def vpn(message: Optional[str] = None, success_message: Optional[str] = None,
        error_message: Optional[str] = None) -> str | Response:
    """
    Route pour l'accès à la page VPN.
    Gère l'affichage de la page VPN pour les utilisateurs habilités.
    Args:
        message (Optional[str]): Message à afficher.
        success_message (Optional[str]): Message de succès à afficher.
        error_message (Optional[str]): Message d'erreur à afficher.
    Returns:
        str | Response: Contenu HTML de la page VPN ou redirection en cas d'erreur.
    """
    habilitation = str(session.get('habilitation', ''))
    return render_template(
        'vpn.html',
        message=message,
        success_message=success_message,
        error_message=error_message,
        habilitation=habilitation
        )


@peraudiere.get('/vpn/download/<access>')
@validate_habilitation(VPN)
def vpn_download(access: str) -> Response | WResponse:
    """
    Route pour le téléchargement d'une configuration VPN.
    Génère et retourne un fichier de configuration WireGuard selon le niveau d'accès.
    Args:
        access (str): Niveau d'accès demandé ('global', 'fichiers', 'charlemagne').
    Returns:
        Response: Fichier de configuration WireGuard ou redirection en cas d'erreur.
    """
    # TODO : implémenter la génération des clés WireGuard éphémères
    # TODO : appeler l'API interne de la VM WireGuard pour enregistrer le peer
    # TODO : retourner le fichier .conf généré en téléchargement
    return redirect(url_for('vpn', error_message='Téléchargement VPN non encore disponible'))


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
    data = request.get_json()
    email: str = data.get('email', '') if data else ''
    try:
        envoi_contrats_renego(email)
        return jsonify(f"Rapport envoye a {email}", 200)
    except (ValueError, OSError, SQLAlchemyError) as e:
        logger.error("Erreur lors de l envoi du rapport a %s : %s", email, e)
        return jsonify(f"Erreur lors de l envoi du rapport a {email} : {e}", 500)
