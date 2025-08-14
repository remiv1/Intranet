from flask import render_template, request, redirect, url_for, session, g
from app import app
from app import docs
from app.models import User, Contract, Event, Document
from typing import List, Dict, Any
from app.__init__ import Session
import hashlib
import datetime
import os
from datetime import timedelta

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

@app.before_request
def before_request():
    g.db_session = Session()

@app.teardown_appcontext
def teardown_request(exception):
    db_session = g.pop('db_session', None)
    if db_session is not None:
        if exception:
            db_session.rollback()
        db_session.close()

@app.route('/')
def home():
    if 'prenom' in session and 'nom' in session:
        prenom = session['prenom']
        nom = session['nom']
        habilitation = session['habilitation']
        
        # création d'une liste de niveaux d'habilitation
        habilitation_levels = list(map(int, str(habilitation)))

        sections: List[Dict[str, Any]] = [
            {
                'classe': 1,
                'titre': 'Gestion des droits',
                'descriptif': 'Permet de gérer/créer/supprimer les droits des utilisateurs de l\'Intranet',
                'buttonid': 'Gdr',
                'onclick': 'gestion_droits'
            },
            {
                'classe': 2,
                'titre': 'Gestion des utilisateurs',
                'descriptif': 'Permet de gérer les utilisateurs déjà existant de l\'Intranet',
                'buttonid': 'Gdu',
                'onclick': 'gestion_utilisateurs'
            },
            {
                'classe': 2,
                'titre': 'Gestion des contrats',
                'descriptif': 'Permet de gérer/accéder aaux contrats en cours pour l\'établissement et d\'en gérer les documents et évènements',
                'buttonid': 'Ddc',
                'onclick': 'contrats'
            },
            {
                'classe': 3,
                'titre': 'Espace réservé',
                'descriptif': 'Espace réservé pour les professeurs principaux des classes (en construction)',
                'buttonid': 'Erpp',
                'onclick': 'erpp'
            },
            {
                'classe': 4,
                'titre': 'Espace réservé',
                'descriptif': 'Espace réservé pour les professeurs de l\'établissement (en construction)',
                'buttonid': 'Erp',
                'onclick': 'erp'
            },
            {
                'classe': 6,
                'titre': 'Espace impressions',
                'descriptif': 'Espace de lancement des impressions à distance',
                'buttonid': 'Ei',
                'onclick': 'ei'
            },
            {
                'classe': 5,
                'titre': 'Espace réservé',
                'descriptif': 'Espace réservé pour les élèves de l\'établissement (en construction)',
                'buttonid': 'Ere',
                'onclick': 'ere'
            }
        ]

        return render_template('index.html', prenom=prenom, nom=nom, habilitation_levels=habilitation_levels, sections=sections)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = request.args.get('message', '')
    if request.method == 'POST':
        try:
            # récupération du contenu du formulaire
            username = request.form.get('username')
            password: str = request.form.get('password', '')
            password = hashlib.sha256(password.encode()).hexdigest()

            # recherche de l'utilisateur dans la base de données
            user = g.db_session.query(User).filter(User.identifiant == username).first()

            # Vérifier si l'utilisateur existe et si le mot de passe est correct
            if user and user.shaMdp == password:
                try:
                    # Stocker les informations de l'utilisateur dans la session
                    session['identifiant'] = username
                    session['prenom'] = user.prenom
                    session['nom'] = user.nom
                    session['mail'] = user.mail
                    session['habilitation'] = user.habilitation
                    user.falseTest=0
                    g.db_session.commit()
                    return redirect(url_for('home'))
                except Exception as e:
                    g.db_session.rollback()
                    mes = f'Erreur {e} lors de la connexion, veuillez réessayer.'
            elif not user:
                mes=f'L\'utilisateur {username} semble inconnu'
            else:
                try:
                    if user.falseTest == '' or user.falseTest == 0:
                        user.falseTest =1
                        reste = 2
                        g.db_session.commit()
                        mes = f'Erreur d\'identifiant ou de mot de passe, il vous reste {reste} essais.'
                    elif user.falseTest >= 2:
                        user.locked = True
                        user.falseTest = 3
                        g.db_session.commit()
                        mes = f'Utilisateur {username} vérouillé, merci de contacter votre administrateur.'
                    else:
                        user.falseTest += 1
                        g.db_session.commit()
                        reste = 3 - user.falseTest
                        mes = f'Erreur d\'identifiant ou de mot de passe, il vous reste {reste} essais.'
                except Exception as e:
                    g.db_session.rollback()
                    mes = f'Erreur lors de la mise à jour du compteur d\'essais.'
            return redirect(url_for('login', message=mes))
        except Exception as e:
            g.db_session.rollback()
            message = f'Erreur lors de la connexion, veuillez réessayer.'
            return redirect(url_for('login', message=message))
    else:
        return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/gestion_droits')
def gestion_droits():
    if '1' in str(session['habilitation']): 
        users = g.db_session.query(User).all()
        return render_template('gestion_droits.html', users=users)
    else:
        return redirect(url_for('logout'))

@app.route('/gestion_utilisateurs')
def gestion_utilisateurs():
    if '2' in str(session['habilitation']): 
        users = g.db_session.query(User).all()
        users.sort(key=lambda x: (x.nom, x.prenom))
        return render_template('gestion_utilisateurs.html', users=users)
    else:
        return redirect(url_for('logout'))

@app.route('/gestion_documents')
def gestion_documents():
    if '2' in str(session['habilitation']):
        return render_template('gestion_documents.html')
    else:
        return redirect(url_for('logout'))

@app.route('/erpp')
def erpp():
    if '3' in str(session['habilitation']):
        return render_template('erpp.html')
    else:
        return redirect(url_for('logout'))

@app.route('/erp')
def erp():
    if '4' in str(session['habilitation']): 
        return render_template('erp.html')
    else:
        return redirect(url_for('logout'))

@app.route('/ei')
def ei():
    if '6' in str(session['habilitation']):
        return render_template('ei.html')
    else:
        return redirect(url_for('logout'))

@app.route('/print_doc', methods=['POST'])
def print_doc():
    if '6' in str(session['habilitation']):
        BinaryDocument = request.files['document']
        document = BinaryDocument.filename
        extension = os.path.splitext(document)[1]
        docname = document.split('.')[0]
        username = session['prenom'] + ' ' + session['nom']
        copies = str(request.form.get('copies'))
        sides = request.form.get('recto_verso')
        media = request.form.get('format')
        orientation = request.form.get('orientation')
        color = request.form.get('couleur')

        #Envoi du document à l'imprimante
        docs.print_document(BinaryDocument,docname, extension, copies, username, sides, media, orientation, color)

        #Suppression du document sur le serveur
        docs.delete_file(docname, extension)

        return redirect(url_for('ei', message='Impression envoyée'))
    else:
        return redirect(url_for('logout'))

@app.route('/ere')
def ere():
    if '5' in str(session['habilitation']):
        return render_template('ere.html')
    else:
        return redirect(url_for('logout'))

@app.route('/ajout_utilisateurs', methods=['POST'])
def ajout_utilisateurs():
    if '1' in str(session['habilitation']): 
        try:
            #Récupération des données du formulaire
            prenom = request.form.get('prenom')
            nom = request.form.get('nom')
            mail = request.form.get('mail')
            identifiant = request.form.get('identifiant')
            mdp = request.form.get('mdp')
            mdp = hashlib.sha256(mdp.encode()).hexdigest()

            #Création du niveau d'habilitation
            habilitation_values = []
            for key, value in request.form.items():
                if key.startswith('habil'):
                    habilitation_values.append(value)
        
            #Trier les valeurs d'habilitation
            sorted_habil = sorted(habilitation_values, key=int)

            #Concaténation des valeurs d'habilitation
            habilitation = int(''.join(sorted_habil))

            user = User(prenom=prenom, nom=nom, identifiant=identifiant, mail=mail, habilitation=habilitation, shaMdp=mdp)
            g.db_session.add(user)
            g.db_session.commit()

            return redirect(url_for('gestion_utilisateurs'))
        except Exception as e:
            g.db_session.rollback()
            return redirect(url_for('gestion_utilisateurs'))
    else: 
        return redirect(url_for('logout'))

@app.route('/suppr_utilisateurs', methods=['POST'])
def suppr_utilisateurs():
    if '1' in str(session['habilitation']): 
        try:
            identifiant = request.form.get('identifiant')
            user = g.db_session.query(User).filter(User.identifiant == identifiant).first()
            if user:
                g.db_session.delete(user)
                g.db_session.commit()
            return redirect(url_for('gestion_utilisateurs'))
        except Exception as e:
            g.db_session.rollback()
            return redirect(url_for('gestion_utilisateurs'))
    else:
        return redirect(url_for('logout'))

@app.route('/modif_utilisateurs', methods=['POST'])
def modif_utilisateurs():
    if '1' in str(session['habilitation']) or '2' in str(session['habilitation']): 
        try:
            prenom = request.form.get('prenom')
            nom = request.form.get('nom')
            mail = request.form.get('mail')
            identifiant = request.form.get('identifiant')
            mdp = request.form.get('mdp')
            mdp = hashlib.sha256(mdp.encode()).hexdigest()
            if request.form.get('unlock'):
                unlock = int(request.form.get('unlock'))
            else:
                unlock = 0

            #Création du niveau d'habilitation
            habilitation_values = []
            for key, value in request.form.items():
                if key.startswith('habil'):
                    habilitation_values.append(value)

            #Trier les valeurs d'habilitation
            sorted_habil = sorted(habilitation_values, key=int)

            #Concaténation des valeurs d'habilitation
            habilitation = int(''.join(sorted_habil))

            #Récupération de l'utilisateur
            user = g.db_session.query(User).filter(User.identifiant == identifiant).first()

            if user:
                # Modification des informations de l'utilisateur
                user.prenom = prenom
                user.nom = nom
                user.mail = mail
                user.identifiant = identifiant
                if mdp != '': 
                    user.shaMdp = mdp
                
                if unlock == 1:
                    user.falseTest = 0
                    user.locked = False

                user.habilitation = habilitation

                g.db_session.commit()

            return redirect(url_for('gestion_utilisateurs'))
        except Exception as e:
            g.db_session.rollback()
            return redirect(url_for('gestion_utilisateurs'))
    else:
        return redirect(url_for('logout'))

@app.route('/gestion_droits', methods=['POST'])
def gestion_droits_post():
    if '1' in str(session['habilitation']) or '2' in str(session['habilitation']): 
        try:
            identifiant = request.form.get('identifiant')
            mdp = request.form.get('mdp')
            mdp = hashlib.sha256(mdp.encode()).hexdigest()
            
            #Création du niveau d'habilitation
            habilitation_values = []
            for key, value in request.form.items():
                if key.startswith('habil'):
                    habilitation_values.append(value)
            
            #Trier les valeurs d'habilitation
            sorted_habil = sorted(habilitation_values, key=int)

            #Concaténation des valeurs d'habilitation
            habilitation = int(''.join(sorted_habil))

            user = g.db_session.query(User).filter(User.identifiant == identifiant).first()
            if user:
                if mdp != '':
                    user.shaMdp = mdp
                user.habilitation = habilitation

                g.db_session.commit()

            return redirect(url_for('gestion_droits'))
        except Exception as e:
            g.db_session.rollback()
            return redirect(url_for('gestion_droits'))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats', methods=['GET', 'POST'])
def contrats():
    if '2' in str(session['habilitation']):
        if request.method == 'GET':
            contracts = g.db_session.query(Contract).all()
            return render_template('contrats.html', contracts=contracts)
        
        if request.method == 'POST':
            try:
                #Récupération des données du formulaire*
                Type = request.form.get('Type0')
                SType = request.form.get('SType0')
                entreprise = request.form.get('Entreprise')
                numContratExterne = request.form.get('numContratExterne')
                intitule = request.form.get('Intitule')
                dateDebut = request.form.get('dateDebut')
                dateFinPreavis = request.form.get('dateFinPreavis')
                dateFin = request.form.get('dateFin')

                if dateFin != '': 
                    contract = Contract(Type = Type, SType = SType, entreprise = entreprise, numContratExterne = numContratExterne, intitule = intitule, dateDebut = dateDebut, dateFin = dateFin, dateFinPreavis = dateFinPreavis)
                else: 
                    contract = Contract(Type = Type, SType = SType, entreprise = entreprise, numContratExterne = numContratExterne, intitule = intitule, dateDebut = dateDebut, dateFinPreavis = dateFinPreavis)
                
                g.db_session.add(contract)
                g.db_session.commit()

                return redirect(url_for('contrats'))
            except Exception as e:
                g.db_session.rollback()
                return redirect(url_for('contrats'))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/<numContrat>', methods=['GET', 'POST'])
def contrats_by_num(numContrat):
    if request.method == 'GET': 
        contract = g.db_session.query(Contract).filter(Contract.id == numContrat).first()
        events = g.db_session.query(Event).filter(Event.idContrat == numContrat)
        documents = g.db_session.query(Document).filter(Document.idContrat == numContrat)

        return render_template('contrat_detail.html', contract = contract, events = events, documents = documents)
    elif request.method == 'POST' and request.form.get('_method') == 'PUT':
        try:
            contract = g.db_session.query(Contract).filter(Contract.id == numContrat).first()
            if contract:
                contract.Type = request.form.get(f'Type{numContrat}')
                contract.SType = request.form.get(f'SType{numContrat}')
                contract.Entreprise = request.form.get(f'Entreprise{numContrat}')
                contract.numContratExterne = request.form.get(f'numContratExterne{numContrat}')
                contract.Intitule = request.form.get(f'Intitule{numContrat}')
                contract.dateDebut = request.form.get(f'dateDebut{numContrat}')
                contract.dateFinPreavis = request.form.get(f'dateFinPreavis{numContrat}')
                if request.form.get(f'dateFin{numContrat}') != '':
                    contract.dateFin = request.form.get(f'dateFin{numContrat}')
            
                g.db_session.commit()

            return redirect(url_for('contrats'))
        except Exception as e:
            g.db_session.rollback()
            return redirect(url_for('contrats'))

@app.route('/contrats/<numContrat>/evenement', methods=['POST'])
def add_contrats_event(numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST':
            try:
                #Récupération des données du formulaire*
                idContrat = request.form.get('idContratE')
                dateEvenement = request.form.get('dateEvenementE')
                Type = request.form.get('TypeE0')
                SType = request.form.get('STypeE0')
                descriptif = request.form.get('descriptifE')

                event = Event(idContrat = idContrat, dateEvenement = dateEvenement, Type = Type, SType = SType, descriptif = descriptif)
                
                g.db_session.add(event)
                g.db_session.commit()

                return redirect(url_for('contrats_by_num', numContrat=idContrat))
            except Exception as e:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat=numContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/<numContrat>/document', methods=['POST'])
def add_contrats_document(numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST':
            try:
                #Récupération du dernier élément
                last_doc = g.db_session.query(Document).order_by(Document.id.desc()).first()
                if last_doc:
                    id = last_doc.id + 1
                else:
                    id = 1

                #Récupération des données du formulaire
                idContrat = request.form.get('idContratD')
                dateDocument = request.form.get('dateDocumentD')
                Type = request.form.get('TypeD0')
                SType = request.form.get('STypeD0')
                descriptif = request.form.get('descriptifD')
                DocumentBinaire = request.files['documentD']
                extention = os.path.splitext(DocumentBinaire.filename)[1]
                name = docs.create_name(dateDocument, idContrat, id, SType)
                LienDocument = name + extention

                #Création du document dans la base de données
                document = Document(idContrat = idContrat, Type = Type, SType = SType, descriptif = descriptif, strLien = LienDocument, dateDocument = dateDocument, name = name)
                
                #Ajout et Fermeture de la session
                g.db_session.add(document)
                g.db_session.commit()

                #Enregistrement du fichier sur le serveur
                docs.upload_file(DocumentBinaire, name, extention)

                #Retour du formulaire
                return redirect(url_for('contrats_by_num', numContrat=idContrat))
            except Exception as e:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat=numContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/numContrat/<numContrat>/numEvenement/<numEvent>', methods=['POST'])
def modif_event_id(numEvent, numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST' and request.form.get('_method') == 'PUT':
            try:
                #Récupération de l'évènement
                event = g.db_session.query(Event).filter(Event.id == numEvent).first()

                if event:
                    #Récupération formulaire
                    idContrat = request.form.get(f'idContratE{numEvent}')
                    event.idContrat = request.form.get(f'idContratE{numEvent}')
                    event.dateEvenement = request.form.get(f'dateEvenementE{numEvent}')
                    event.Type = request.form.get(f'TypeE{numEvent}')
                    event.SType = request.form.get(f'STypeE{numEvent}')
                    event.descriptif = request.form.get(f'descriptifE{numEvent}')

                    #Retour
                    g.db_session.commit()

                    return redirect(url_for('contrats_by_num', numContrat = idContrat))
            except Exception as e:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat = numContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/numContrat/<numContrat>/numDocument/<numDoc>', methods=['POST'])
def modif_document_id(numDoc, numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST' and request.form.get('_method') == 'PUT':
            try:
                #Récupération du document
                document = g.db_session.query(Document).filter(Document.id == numDoc).first()

                if document:
                    #Récupération formulaire
                    id = document.id
                    idContrat = request.form.get(f'idContratD{numDoc}')
                    dateDocument = request.form.get(f'dateDocumentD{numDoc}')
                    document.dateDocument = dateDocument
                    Type = request.form.get(f'TypeD{numDoc}')
                    document.Type = Type
                    SType = request.form.get(f'STypeD{numDoc}')
                    document.SType = SType
                    document.descriptif = request.form.get(f'descriptifD{numDoc}')
                    if request.files[f'documentD{numDoc}']:
                        DocumentBinaire = request.files[f'documentD{numDoc}']
                        name = docs.create_name(dateDocument, idContrat, id, SType)
                        extention = os.path.splitext(DocumentBinaire.filename)[1]
                    else:
                        strLien = request.form.get(f'strLienD{numDoc}')
                        completName = strLien.split('_')[3]
                        name = docs.create_name(dateDocument, idContrat, id, SType)
                        extention = completName.split('.')[1]
                    LienDocument = name + extention
                    document.strLien = LienDocument

                    # création d'un nom de document
                    date_date = datetime.datetime.strptime(dateDocument, '%Y-%m-%d').date()
                    str_date = date_date.strftime('%y%m%d')
                    str_idContrat = str(idContrat).zfill(6)
                    str_idDocument = str(id).zfill(6)
                    str_SType = SType[:5]
                    name = f"{str_date}_{str_idContrat}_{str_idDocument}_{str_SType}"

                    #Gestion automatique du nom de document
                    document.name = name

                    #Retour
                    g.db_session.commit()

                    return redirect(url_for('contrats_by_num', numContrat = idContrat))
            except Exception as e:
                g.db_session.rollback()
                return redirect(url_for('contrats_by_num', numContrat = numContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/numContrat/<numContrat>/numDocument/<numDoc>/download/<name>', methods=['GET'])
def download_document(numDoc, numContrat, name:str):
    if '2' in str(session['habilitation']):
        extention = name.split('.')[1]
        name = name.split('.')[0]
        return docs.download_file(file_name=name, extension=extention)
    else:
        return redirect(url_for('logout'))
