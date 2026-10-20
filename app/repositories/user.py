"""Module de gestion des utilisateurs, incluant les méthodes pour l'authentification,
le verrouillage de compte et la gestion des messages d'erreur liés à l'authentification.
Ce module utilise SQLAlchemy pour interagir avec la base de données et Flask pour gérer les
sessions et les redirections.
"""

from datetime import date
from hashlib import sha256
from hmac import compare_digest
from urllib.parse import unquote, urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from flask import g, session, redirect, url_for, Request, Response, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.wrappers.response import Response as WerkzeugResponse

from app.models import User
from app.config.logger import api_logger
from app.repositories.auth_session import create_auth_session, SessionStorageError

_PASSWORD_HASHER = PasswordHasher()


def hash_password(password: str) -> str:
    """Cree un hash Argon2id avec un sel aleatoire et les parametres courants.

    Args:
        password: Mot de passe fourni par le formulaire.

    Returns:
        str: Hash encode contenant le format, les parametres et le sel.
    """
    return _PASSWORD_HASHER.hash(password)


def _verify_password(stored_hash: str | None, password: str) -> bool:
    if not stored_hash:
        return False
    if stored_hash.startswith('$argon2id$'):
        try:
            return _PASSWORD_HASHER.verify(stored_hash, password)
        except (InvalidHashError, VerificationError):
            return False
    if len(stored_hash) == 64 and all(
        character in '0123456789abcdefABCDEF' for character in stored_hash
    ):
        return compare_digest(stored_hash.lower(), sha256(password.encode()).hexdigest())
    return False


def get_local_redirect_url(redirect_url: str | None) -> str | None:
    """Valide un chemin local sans modifier ses parametres ou son fragment.

    Args:
        redirect_url: Destination provenant de la requete ou du formulaire.

    Returns:
        str | None: Destination originale valide, ou None si elle est dangereuse.
    """
    if not redirect_url:
        return None
    candidate = redirect_url
    try:
        for _ in range(5):
            parsed = urlsplit(candidate)
            is_local = (
                candidate.startswith('/') and not candidate.startswith('//')
                and not parsed.scheme and not parsed.netloc
            )
            if not is_local or '\\' in candidate or any(
                ord(character) < 32 or ord(character) == 127 for character in candidate
            ):
                return None
            decoded = unquote(candidate, errors='strict')
            if decoded == candidate:
                return redirect_url
            candidate = decoded
    except ValueError:
        return None
    return None


def handle_login_post() -> Response | WerkzeugResponse:
    """
    Gère la logique POST de la route login.
    Returns:
        Response | WerkzeugResponse: La redirection appropriée selon le résultat de l'auth.
    """
    try:
        # Récupération de l'URL de redirection depuis le formulaire
        redirect_url = request.form.get('preview_request', None)

        # récupération du contenu du formulaire
        user, _, password = UsersMethods.get_user_from_credentials(request)

        # Vérifier si l'utilisateur existe et si le mot de passe est correct
        if UsersMethods.valid_authentication(user, password):
            return UsersMethods.handle_login_redirect(redirect_url, success=True)

        # Vérifier les conditions de blocage de l'utilisateur
        validation_message = UsersMethods.get_user_validation_message(user)
        if validation_message:
            return UsersMethods.handle_login_redirect(
                redirect_url,
                error_message=validation_message
                )

        # Gestion des erreurs de mots de passe
        error_message = UsersMethods.generate_nb_false_pwd(user)
        return UsersMethods.handle_login_redirect(redirect_url, error_message=error_message)

    except SessionStorageError:
        session.clear()
        response = jsonify(error="Connexion indisponible : impossible d'enregistrer la session.")
        response.status_code = 503
        return response
    except (ValueError, KeyError, AttributeError) as e:
        # Récupération de l'URL de redirection depuis le formulaire en cas d'erreur
        redirect_url = request.form.get('preview_request', None)
        # En cas d'erreur, retour sur la page de connexion après rollback
        error_message = f'Erreur lors de la connexion, veuillez réessayer : {e}'
        return UsersMethods.handle_login_redirect(redirect_url, error_message=error_message)


class UsersMethods:
    """
    Classe pour gérer les méthodes liées aux utilisateurs.
    Méthodes statiques:
        get_user_from_credentials:
            Récupère un utilisateur à partir des identifiants fournis dans une requête.
        valid_authentication:
            Valide l'authentification d'un utilisateur et initialise la session.
        generate_nb_false_pwd:
            Gère le compteur d'essais de mot de passe incorrects et verrouille
            l'utilisateur si nécessaire.
        get_user_validation_message:
            Retourne le message d'erreur approprié selon l'état de l'utilisateur.
        handle_login_redirect:
            Gère la redirection après une tentative de connexion.
    """
    @staticmethod
    def get_user_from_credentials(req: Request) -> tuple[User | None, str, str]:
        """
        Récupère un utilisateur à partir des identifiants fournis dans une requête.
        Args:
            req (Request): La requête contenant les identifiants :
                - 'username' : nom d'utilisateur
                - 'password' : mot de passe
        Returns:
            tuple[User | None, str, str]: L'utilisateur eventuel, son identifiant et
                le mot de passe saisi, non prehache.
        """
        # Récupération du credential
        username = req.form.get('username', '')
        password = req.form.get('password', '')

        try:
            # Recherche de l'utilisateur dans la base de données
            user = g.db_session.query(User).filter(User.identifiant == username).first()

        except SQLAlchemyError:
            g.db_session.rollback()
            user = None

        # Retourne les identifiants de l'utilisateur et l'utilisateur
        return user, username, password

    @staticmethod
    def valid_authentication(user: User | None, password: str) -> bool:
        """
        Valide l'authentification d'un utilisateur et initialise la session.
        Args:
            user (User): L'utilisateur à valider.
            password (str): Le mot de passe fourni pour la validation.
        Returns:
            bool: True si l'authentification est réussie, False sinon.
        """
        if user is None or user.locked:
            return False
        if user.fin and user.fin <= date.today():
            return False
        if user.debut and user.debut > date.today():
            return False
        if not _verify_password(user.sha_mdp, password):
            return False

        identity: dict[str, str | int | None] = {
            'identifiant': user.identifiant,
            'prenom': user.prenom,
            'nom': user.nom,
            'mail': user.mail,
            'habilitation': str(user.habilitation),
            'id': user.id,
        }
        needs_upgrade = not user.sha_mdp.startswith('$argon2id$') \
            or _PASSWORD_HASHER.check_needs_rehash(user.sha_mdp)
        try:
            if needs_upgrade:
                user.sha_mdp = hash_password(password)
            user.false_test = 0
            g.db_session.commit()
        except SQLAlchemyError as error:
            g.db_session.rollback()
            api_logger.warning(
                'MIGR-AUTH echec de persistance user_id=%s operation=%s erreur=%s code=%s ; '
                'connexion autorisee apres rollback',
                identity['id'], 'rehash' if needs_upgrade else 'compteur',
                type(error).__name__, getattr(getattr(error, 'orig', None), 'errno', None),
            )
        try:
            token = create_auth_session(g.db_session, user.id, session.get('auth_token'))
            g.db_session.commit()
        except SQLAlchemyError:
            g.db_session.rollback()
            api_logger.error('SESSION-AUTH echec de creation user_id=%s', identity['id'])
            raise SessionStorageError from None
        session.clear()
        session.update(identity)
        session['auth_token'] = token
        session.permanent = True
        return True

    @staticmethod
    def generate_nb_false_pwd(user: User | None) -> str:
        """
        Gère le compteur d'essais de MdP incorrects et verrouille l'utilisateur si nécessaire.
        Args:
            user (User): L'utilisateur pour lequel gérer le compteur d'essais.
        Returns:
            str: Un message indiquant le résultat de l'opération.
        """
        if user is None:
            return "Erreur d'identifiant ou de mot de passe."
        if not user.false_test:
            user.false_test = 0
        if user.false_test < 2:
            user.false_test += 1
            reste = 3 - (user.false_test or 0)
            message = f'Erreur d\'identifiant ou de mot de passe, il vous reste {reste} essais.'
        else:
            user.locked = True
            user.false_test = 3
            message = f'Utilisateur {user.nom} vérouillé, merci de contacter votre administrateur.'
        try:
            g.db_session.commit()
        except SQLAlchemyError as e:
            message = f'Erreur lors de la mise à jour du compteur d\'essais : {e}'
        return message

    @staticmethod
    def get_user_validation_message(user: User | None) -> str | None:
        """
        Retourne le message d'erreur approprié selon l'état de l'utilisateur.
        Args:
            user (User): L'utilisateur à valider.
        Returns:
            str | None: Le message d'erreur ou None si l'utilisateur est valide.
        """
        if user is None:
            return None
        if user.locked:
            return 'Votre compte est verrouillé, veuillez contacter votre administrateur.'
        if user.fin and user.fin <= date.today():
            return 'Votre compte a expiré, veuillez contacter votre administrateur.'
        if user.debut and user.debut > date.today():
            return "Votre compte n'est pas encore actif."
        return None

    @staticmethod
    def handle_login_redirect(
            redirect_url: str | None,
            success: bool = False,
            error_message: str | None = None
        ) -> Response | WerkzeugResponse:
        """
        Gère la redirection après une tentative de connexion.
        Args:
            redirect_url (str | None): L'URL de redirection originale.
            success (bool): True si la connexion a réussi.
            error_message (str | None): Message d'erreur à afficher.
        Returns:
            Response | WerkzeugResponse: La redirection appropriée.
        """
        redirect_url = get_local_redirect_url(redirect_url)
        if success:
            if redirect_url:
                return redirect(redirect_url)
            return redirect(url_for('home', success_message='Connexion réussie'))

        return redirect(url_for('login', error_message=error_message, preview_request=redirect_url))
