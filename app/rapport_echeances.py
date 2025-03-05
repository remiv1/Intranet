import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import and_
import smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from app import db_session
from config import Config
from models import Contract

def envoi_contrats_renego(mail: str):
    # Connexion à la base de données
    conn = db_session.connection()

    # Calcul des dates limites
    date_4_mois = (datetime.now() + timedelta(days=4*30)).strftime('%Y-%m-%d')
    date_6_mois = (datetime.now() + timedelta(days=6*30)).strftime('%Y-%m-%d')

    #Extraction des contrats
    contracts = conn.query(Contract).filter(and_(Contract.dateFinPreavis >= date_4_mois, Contract.dateFinPreavis <= date_6_mois)).all()
    if contracts:
        data = [
            {
                'id' : contract.id,
                'Type': contract.Type,
                'SType': contract.SType,
                'Entreprise': contract.Entreprise,
                'numContratExterne': contract.numContratExterne,
                'Intitule': contract.Intitule,
                'dateDebut': contract.dateDebut,
                'dateFinPreavis': contract.dateFinPreavis,
                'dateFin': contract.dateFin
            }
            for contract in contracts
        ]
        df = pd.DataFrame(data)
        fichier_excel = 'contrats_a_renegocier.xlsx'
        df.to_excel(fichier_excel, index=False)

        # Configuration de l'e-mail
        email_expediteur = Config.MAIL_USERNAME
        email_destinataire = mail
        mot_de_passe = Config.MAIL_PASSWORD

        msg = MIMEMultipart()
        msg['From'] = email_expediteur
        msg['To'] = email_destinataire
        msg['Subject'] = 'IMPORTANT - Liste hebdomadaire des contrats à renégocier'

        body = 'Veuillez trouver en pièce jointe la liste des contrats à renégocier.'
        msg.attach(MIMEText(body, 'plain'))

        # Ajouter le fichier Excel en pièce jointe
        with open(fichier_excel, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={fichier_excel}',
            )
            msg.attach(part)

        # Envoyer l'e-mail
        try:
            with smtplib.SMTP(Config.EMAIL_SMTP, Config.EMAIL_PORT) as server:
                server.starttls()
                server.login(email_expediteur, mot_de_passe)
                server.send_message(msg)
            print("E-mail envoyé avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'e-mail : {e}")
        finally:
            conn.close()
            os.remove(fichier_excel)
    else:
        conn.close()