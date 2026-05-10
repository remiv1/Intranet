"""Module de génération et d'envoi du rapport des échéances de contrats à renégocier.
Ce module contient la fonction `envoi_contrats_renego` qui :
1. Se connecte à la base de données pour extraire les contrats dont la date de fin de préavis
   est comprise entre 4 et 6 mois à partir de la date actuelle.
2. Génère un e-mail formaté avec la liste de ces contrats, en utilisant un template HTML.
3. Envoie cet e-mail à une adresse spécifiée en utilisant les paramètres de messagerie
   configurés dans l'application.
Le module utilise SQLAlchemy pour les requêtes de base de données, Jinja2 pour le
rendu du template d'e-mail, et smtplib pour l'envoi de l'e-mail.
Il inclut également une gestion des erreurs robuste pour assurer la fiabilité de l'envoi
des rapports, avec des logs détaillés pour faciliter le dépannage en cas de problème.
"""

from datetime import datetime, timedelta
from logging import getLogger
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy import and_
from flask import g, render_template
from .config import Config
from .models import Contract

logger = getLogger(__name__)

def envoi_contrats_renego(mail: str):
    """
    Envoie un rapport des contrats à renégocier par e-mail.
    Arguments:
        mail (str): L'adresse e-mail du destinataire.
    Retourne:
        None
    """
    # Connexion à la base de données
    conn = g.db_session

    # Calcul des dates limites
    date_4_mois = (datetime.now() + timedelta(days=4*30)).strftime('%Y-%m-%d')
    date_6_mois = (datetime.now() + timedelta(days=6*30)).strftime('%Y-%m-%d')

    # Extraction des contrats
    contracts = conn.query(Contract) \
                    .filter(and_(
                        Contract.date_fin_preavis >= date_4_mois,
                        Contract.date_fin_preavis <= date_6_mois
                    )) \
                    .all()
    logger.info("Nombre de contrats à renégocier trouvés : %s", len(contracts))
    if contracts:
        # Configuration de l'e-mail
        email_expediteur: str = Config.EMAIL_USER
        mot_de_passe: str = Config.EMAIL_PASSWORD

        logger.info("Préparation de l'envoi de l'e-mail à %s", mail)

        msg = MIMEMultipart()
        msg['From'] = email_expediteur
        msg['To'] = mail
        msg['Subject'] = 'IMPORTANT - Liste hebdomadaire des contrats à renégocier'

        body = render_template('mail_echeance.html', date_4_mois=date_4_mois,
                           date_6_mois=date_6_mois, contrats=contracts)
        logger.info("Corps de l'e-mail généré avec succès.")
        msg.attach(MIMEText(body, 'html'))

        # Envoyer l'e-mail
        try:
            with smtplib.SMTP(Config.EMAIL_SMTP, Config.EMAIL_PORT) as server:
                server.starttls()
                server.login(email_expediteur, mot_de_passe)
                server.send_message(msg)
            logger.info("E-mail envoye avec succes a %s", mail)
        except Exception as e:
            logger.error("Erreur lors de l envoi de l e-mail : %s", e)
        finally:
            conn.close()
    else:
        conn.close()
        logger.info(
            "Aucun contrat à renégocier trouvé entre %s et %s", date_4_mois, date_6_mois
        )
