"""Module de gestion des utilisateurs, incluant les méthodes pour l'authentification,
le verrouillage de compte et la gestion des messages d'erreur liés à l'authentification.
Ce module utilise SQLAlchemy pour interagir avec la base de données et Flask pour gérer les
sessions et les redirections.
"""

from datetime import datetime
from hashlib import sha256
from typing import Any, Tuple
from flask import g, session, redirect, url_for, Request, Response, request
from sqlalchemy.exc import SQLAlchemyError
from app.models import User


def handle_login_post() -> Response:
    """
    Gère la logique POST de la route login.
    Returns:
        Response: La redirection appropriée selon le résultat de l'authentification.
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
    def get_user_from_credentials(req: Request) -> Tuple[User, str, str]:
        """
        Récupère un utilisateur à partir des identifiants fournis dans une requête.
        Args:
            req (Request): La requête contenant les identifiants :
                - 'username' : nom d'utilisateur
                - 'password' : mot de passe
        Returns:
            Tuple[User, str, str]: Un tuple contenant l'utilisateur, le nom d'utilisateur
                                   et le mot de passe.
        """
        # Récupération du credential
        username = req.form.get('username', '')
        password = req.form.get('password', '')
        password = sha256(password.encode()).hexdigest()

        try:
            # Recherche de l'utilisateur dans la base de données
            user = g.db_session.query(User).filter(User.identifiant == username).first()

        except SQLAlchemyError:
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
            session['id'] = user.id
            try:
                # Stocker les informations de l'utilisateur dans la session
                user.false_test=0
                g.db_session.commit()
                return True
            except SQLAlchemyError:
                return False
        return False

    @staticmethod
    def generate_nb_false_pwd(user: User) -> str:
        """
        Gère le compteur d'essais de MdP incorrects et verrouille l'utilisateur si nécessaire.
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
        except SQLAlchemyError as e:
            message = f'Erreur lors de la mise à jour du compteur d\'essais : {e}'
        return message

    @staticmethod
    def get_user_validation_message(user: User) -> str | None:
        """
        Retourne le message d'erreur approprié selon l'état de l'utilisateur.
        Args:
            user (User): L'utilisateur à valider.
        Returns:
            str | None: Le message d'erreur ou None si l'utilisateur est valide.
        """
        if user.locked:
            return 'Votre compte est verrouillé, veuillez contacter votre administrateur.'
        elif user.fin and user.fin <= datetime.now():
            return 'Votre compte a expiré, veuillez contacter votre administrateur.'
        return None

    @staticmethod
    def handle_login_redirect(
            redirect_url: str | None,
            success: bool = False,
            error_message: str | None = None
        ) -> Any:
        """
        Gère la redirection après une tentative de connexion.
        Args:
            redirect_url (str | None): L'URL de redirection originale.
            success (bool): True si la connexion a réussi.
            error_message (str | None): Message d'erreur à afficher.
        Returns:
            Response: La redirection appropriée.
        """
        if success:
            if redirect_url and redirect_url != '' and redirect_url != 'None':
                return redirect(redirect_url)
            return redirect(url_for('home', success_message='Connexion réussie'))

        return redirect(url_for('login', error_message=error_message, preview_request=redirect_url))
