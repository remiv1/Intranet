import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import and_
import smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import g
from config import Config
from models import Contract

def envoi_contrats_renego(mail: str):
    # Connexion à la base de données
    conn = g.db_session

    # Calcul des dates limites
    date_4_mois = (datetime.now() + timedelta(days=4*30)).strftime('%Y-%m-%d')
    date_6_mois = (datetime.now() + timedelta(days=6*30)).strftime('%Y-%m-%d')

    # Extraction des contrats
    contracts = conn.query(Contract).filter(and_(Contract.date_fin_preavis >= date_4_mois, Contract.date_fin_preavis <= date_6_mois)).all()
    if contracts:
        data = [
            {
                'id' : contract.id,
                'type_contrat': contract.type_contrat,
                'sous_type_contrat': contract.sous_type_contrat,
                'entreprise': contract.entreprise,
                'id_externe_contrat': contract.id_externe_contrat,
                'intitule': contract.intitule,
                'date_debut': contract.date_debut,
                'date_fin_preavis': contract.date_fin_preavis,
                'date_fin': contract.date_fin
            }
            for contract in contracts
        ]
        df = pd.DataFrame(data)
        fichier_csv = 'contrats_a_renegocier.csv'
        df.to_csv(fichier_csv, index=False)

        # Configuration de l'e-mail
        email_expediteur: str = Config.EMAIL_USER
        email_destinataire: str = mail
        mot_de_passe: str = Config.EMAIL_PASSWORD

        msg = MIMEMultipart()
        msg['From'] = email_expediteur
        msg['To'] = email_destinataire
        msg['Subject'] = 'IMPORTANT - Liste hebdomadaire des contrats à renégocier'

        body = 'Veuillez trouver en pièce jointe la liste des contrats à renégocier.'
        msg.attach(MIMEText(body, 'plain'))

        # Ajouter le fichier Excel en pièce jointe
        with open(fichier_csv, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={fichier_csv}',
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
            os.remove(fichier_csv)
    else:
        conn.close()