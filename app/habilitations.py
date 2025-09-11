'''
API'Raudiere - Définition des niveaux d'habilitation
=============================================

Module de l'application API'Raudiere pour documenter les niveaux d'habilitation.
Cette application web d'organisation fournit une solution intégrée pour la gestion.
Les niveaux d'habilitation sont les suivants :
- Administrateur (1)
- Gestionnaire (2)
- Professeurs Principaux (3)
- Professeurs (4)
- Elèves (5)
- Impressions (6)

Architecture : Flask + SQLAlchemy + MariaDB + MongoDB (logs)
Serveur WSGI : Waitress (production-ready)
Authentification : Sessions sécurisées [avec hachage Argon2 à venir]

Auteur : Rémi Verschuur
Version : 1.1
'''
from functools import wraps
from typing import Callable, Any, List
from flask import session, redirect, url_for

# Définition des niveaux d'habilitation
ADMINISTRATEUR = '1'
GESTIONNAIRE = '2'
PROFESSEURS_PRINCIPAUX = '3'
PROFESSEURS = '4'
ELEVES = '5'
IMPRESSIONS = '6'

def validate_habilitation(required_habilitation: str | List[str]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Décorateur pour valider si l'utilisateur connecté possède une habilitation spécifique.

    Args:
        required_habilitation (str): Habilitation requise (ex: '3').

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: La fonction décorée ou une réponse d'erreur si l'habilitation est manquante.
    """
    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Vérifie si l'utilisateur est connecté et possède une habilitation
            habilitations = session.get('habilitations', '')  # Exemple : '123'
            validate_habilitation = False

            # Si l'habilitation requise est une chaîne de caractères, la convertir en liste
            required_habilitation_list: List[str] = (
                [required_habilitation]
                if isinstance(required_habilitation, str)
                else required_habilitation
            )

            for rh in required_habilitation_list:
                for habilitation in habilitations:
                    if habilitation == rh:
                        validate_habilitation = True
                        break
            if not validate_habilitation:
                return redirect(url_for('logout'))
            return function(*args, **kwargs)
        return wrapper
    return decorator
