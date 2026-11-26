"""Module des utilitaires pour la gestion des signatures et des invitations par e-mail.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import smtplib
import logging
from pathlib import Path
from typing import List

from ..config import ConfigMail

def send_email_invitation(*, to: str, template: str) -> None:
    """Envoie un e-mail d'invitation à signer un document.

    :param to: Adresse e-mail du destinataire.
    :type to: str
    :param template: Contenu HTML de l'e-mail.
    :type template: str

    :raises smtplib.SMTPException: Si l'envoi de l'e-mail échoue.

    :return: None
    :rtype: None
    """
    # Configuration de l'e-mail
    email_expediteur: str = ConfigMail.EMAIL_USER
    mot_de_passe: str = ConfigMail.EMAIL_PASSWORD

    # Construire le message
    msg = MIMEMultipart()
    msg['From'] = email_expediteur
    msg['To'] = to
    msg['Subject'] = 'La Péraudière | Vous êtes invité à signer un document'
    body = template
    msg.attach(MIMEText(body, 'html'))

    # Envoyer l'e-mail
    try:
        with smtplib.SMTP(ConfigMail.EMAIL_SMTP, ConfigMail.EMAIL_PORT) as server:
            server.starttls()
            server.login(email_expediteur, mot_de_passe)
            server.send_message(msg)
    except smtplib.SMTPException as e:
        logging.exception(
            "Erreur lors de l'envoi de l'e-mail d'invitation à %s: %s",
            to,
            str(e)
        )

def send_email_signed_files(*, to: str, template: str, attachments: List[str]) -> None:
    """Envoie un e-mail avec des fichiers signés en pièce jointe.

    :param to: Adresse e-mail du destinataire.
    :type to: str
    :param template: Contenu HTML de l'e-mail.
    :type template: str
    :param attachments: Liste des chemins de fichiers à attacher.
    :type attachments: List[str]

    :raises smtplib.SMTPException: Si l'envoi de l'e-mail échoue.
    :raises FileNotFoundError: Si un fichier joint est introuvable.
    :raises IOError: Si une erreur d'entrée/sortie se produit lors de la lecture d'un fichier joint.

    :return: None
    :rtype: None
    """
    # Configuration de l'e-mail
    email_expediteur: str = ConfigMail.EMAIL_USER
    mot_de_passe: str = ConfigMail.EMAIL_PASSWORD

    # Construire le message
    msg = MIMEMultipart()
    msg['From'] = email_expediteur
    msg['To'] = to
    msg['Subject'] = 'La Péraudière | Documents signés'
    body = template
    msg.attach(MIMEText(body, 'html'))

    # Ajouter toutes les pièces jointes
    for file_path in attachments:
        try:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=Path(file_path).name)
                msg.attach(part)
        except (smtplib.SMTPException, FileNotFoundError, IOError) as e:
            logging.exception(
                "Erreur lors de la lecture de la pièce jointe %s: %s",
                file_path,
                str(e)
            )
            continue
    # Envoyer l'e-mail
    try:
        with smtplib.SMTP(ConfigMail.EMAIL_SMTP, ConfigMail.EMAIL_PORT) as server:
            server.starttls()
            server.login(email_expediteur, mot_de_passe)
            server.send_message(msg)
    except smtplib.SMTPException as e:
        logging.exception(
            "Erreur lors de l'envoi de l'e-mail avec pièces jointes à %s: %s",
            to,
            str(e)
        )

def send_otp_email(*, to: str, template: str) -> None:
    """Envoie un e-mail contenant un code OTP pour la signature.

    :param to: Adresse e-mail du destinataire.
    :type to: str
    :param template: Contenu HTML de l'e-mail.
    :type template: str

    :raises smtplib.SMTPException: Si l'envoi de l'e-mail échoue.

    :return: None
    :rtype: None
    """
    # Configuration de l'e-mail
    email_expediteur: str = ConfigMail.EMAIL_USER
    mot_de_passe: str = ConfigMail.EMAIL_PASSWORD

    # Construire le message
    msg = MIMEMultipart()
    msg['From'] = email_expediteur
    msg['To'] = to
    msg['Subject'] = 'La Péraudière | Votre code OTP pour signer un document'
    body = template
    msg.attach(MIMEText(body, 'html'))

    # Envoyer l'e-mail
    try:
        with smtplib.SMTP(ConfigMail.EMAIL_SMTP, ConfigMail.EMAIL_PORT) as server:
            server.starttls()
            server.login(email_expediteur, mot_de_passe)
            server.send_message(msg)
    except smtplib.SMTPException as e:
        logging.exception(
            "Erreur lors de l'envoi de l'e-mail OTP à %s: %s",
            to,
            str(e)
        )
