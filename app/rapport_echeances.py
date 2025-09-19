from datetime import datetime, timedelta
from sqlalchemy import and_
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import g, render_template
from config import Config
from models import Contract
from logging import getLogger

logger = getLogger(__name__)

def envoi_contrats_renego(mail: str):
    # Connexion à la base de données
    conn = g.db_session

    # Calcul des dates limites
    date_4_mois = (datetime.now() + timedelta(days=4*30)).strftime('%Y-%m-%d')
    date_6_mois = (datetime.now() + timedelta(days=6*30)).strftime('%Y-%m-%d')

    # Extraction des contrats
    contracts = conn.query(Contract).filter(and_(Contract.date_fin_preavis >= date_4_mois, Contract.date_fin_preavis <= date_6_mois)).all()
    logger.info(f"Nombre de contrats à renégocier trouvés : {len(contracts)}")
    if contracts:
        # Configuration de l'e-mail
        email_expediteur: str = Config.EMAIL_USER
        mot_de_passe: str = Config.EMAIL_PASSWORD

        logger.info(f"Préparation de l'envoi de l'e-mail à {mail}")

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
            logger.info(f"E-mail envoye avec succes a {mail}")
        except Exception as e:
            logger.error(f"Erreur lors de l envoi de l e-mail : {e}")
        finally:
            conn.close()
    else:
        conn.close()