"""Module de configuration des mails.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from os import getenv
from dataclasses import dataclass

@dataclass
class ConfigMail:
    """ConfigMail est une class pour la configuration des mails
    
    :param EMAIL_USER: Utilisateur de l'email.
    :type EMAIL_USER: str
    :param EMAIL_PASSWORD: Mot de passe de l'email.
    :type EMAIL_PASSWORD: str
    :param EMAIL_SMTP: Serveur SMTP de l'email.
    :type EMAIL_SMTP: str
    :param EMAIL_PORT: Port du serveur SMTP.
    :type EMAIL_PORT: int
    :param API_MAIL_TOKEN: Token API pour les mails.
    :type API_MAIL_TOKEN: str

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    EMAIL_USER: str = getenv('EMAIL_USER', '') # pylint: disable=C0103
    EMAIL_PASSWORD: str = getenv('EMAIL_PASSWORD', '') # pylint: disable=C0103
    EMAIL_SMTP: str = getenv('EMAIL_SMTP', '') # pylint: disable=C0103
    EMAIL_PORT: int = int(getenv('EMAIL_PORT', '587')) # pylint: disable=C0103
    API_MAIL_TOKEN: str = getenv('API_MAIL_TOKEN', '') # pylint: disable=C0103
