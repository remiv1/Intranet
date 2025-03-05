from flask import render_template, request, redirect, url_for, session
from app import app
from app import docs
from app.models import User, Contract, Event, Document
from app.__init__ import db_session
import hashlib
import datetime
import os

@app.route('/')
def home():
    if 'prenom' in session and 'nom' in session:
        prenom = session['prenom']
        nom = session['nom']
        habilitation = session['habilitation']
        
        # création d'une liste de niveaux d'habilitation
        habilitation_levels = list(map(int, str(habilitation)))

        sections = [
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
    if request.method == 'POST':
        # récupération du contenu du formulaire
        username = request.form.get('username')
        password = request.form.get('password')
        password = hashlib.sha256(password.encode()).hexdigest()

        # recherche de l'utilisateur dans la base de données
        user = db_session.query(User).filter(User.identifiant == username).first()

        # Vérifier si l'utilisateur existe et si le mot de passe est correct
        if user and user.shaMdp == password:
            # Stocker les informations de l'utilisateur dans la session
            session['identifiant'] = username
            session['prenom'] = user.Prenom
            session['nom'] = user.Nom
            session['mail'] = user.mail
            session['habilitation'] = user.habilitation
            return redirect(url_for('home'))
        
        return render_template('login_error.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/gestion_droits')
def gestion_droits():
    if '1' in str(session['habilitation']): 
        users = db_session.query(User).all()
        return render_template('gestion_droits.html', users=users)
    else:
        return redirect(url_for('logout'))

@app.route('/gestion_utilisateurs')
def gestion_utilisateurs():
    if '2' in str(session['habilitation']): 
        users = db_session.query(User).all()
        users.sort(key=lambda x: (x.Nom, x.Prenom))
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

@app.route('/print', methods=['POST'])
def print():
    if '6' in str(session['habilitation']):
        BinaryDocument = request.files['document']
        document = BinaryDocument.filename
        extension = os.path.splitext(document)[1]
        docname = document.split('.')[0]
        username = session['prenom'] + ' ' + session['nom']
        site_name = 'Intranet'
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

        user = User(Prenom=prenom, Nom=nom, identifiant=identifiant, mail=mail, habilitation=habilitation, shaMdp=mdp)
        db_session.add(user)
        db_session.commit()

        return redirect(url_for('gestion_utilisateurs'))
    else: 
        return redirect(url_for('logout'))

@app.route('/suppr_utilisateurs', methods=['POST'])
def suppr_utilisateurs():
    if '1' in str(session['habilitation']): 
        identifiant = request.form.get('identifiant')
        user = db_session.query(User).filter(User.identifiant == identifiant).first()
        db_session.delete(user)
        db_session.commit()

        return redirect(url_for('gestion_utilisateurs'))
    else:
        return redirect(url_for('logout'))

@app.route('/modif_utilisateurs', methods=['POST'])
def modif_utilisateurs():
    if '1' in str(session['habilitation']) or '2' in str(session['habilitation']): 

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

        user = db_session.query(User).filter(User.identifiant == identifiant).first()

        user.Prenom = prenom
        user.Nom = nom
        user.mail = mail
        user.identifiant = identifiant
        if mdp != '': 
            user.shaMdp = mdp
        user.habilitation = habilitation

        db_session.commit()

        return redirect(url_for('gestion_utilisateurs'))
    else:
        return redirect(url_for('logout'))

@app.route('/gestion_droits', methods=['POST'])
def gestion_droits_post():
    if '1' in str(session['habilitation']) or '2' in str(session['habilitation']): 
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

        user = db_session.query(User).filter(User.identifiant == identifiant).first()
        if mdp != '':
            user.shaMdp = mdp
        user.habilitation = habilitation

        db_session.commit()

        return redirect(url_for('gestion_droits'))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats', methods=['GET', 'POST'])
def contrats():
    if '2' in str(session['habilitation']):
        if request.method == 'GET':
            contracts = db_session.query(Contract).all()
            return render_template('contrats.html', contracts=contracts)
        
        if request.method == 'POST':
            #Récupération des données du formulaire*
            Type = request.form.get('Type0')
            SType = request.form.get('SType0')
            Entreprise = request.form.get('Entreprise')
            numContratExterne = request.form.get('numContratExterne')
            Intitule = request.form.get('Intitule')
            dateDebut = request.form.get('dateDebut')
            dateFinPreavis = request.form.get('dateFinPreavis')
            dateFin = request.form.get('dateFin')

            if dateFin != '': 
                contract = Contract(Type = Type, SType = SType, Entreprise = Entreprise, numContratExterne = numContratExterne, Intitule = Intitule, dateDebut = dateDebut, dateFin = dateFin, dateFinPreavis = dateFinPreavis)
            else: 
                contract = Contract(Type = Type, SType = SType, Entreprise = Entreprise, numContratExterne = numContratExterne, Intitule = Intitule, dateDebut = dateDebut, dateFinPreavis = dateFinPreavis)
            
            db_session.add(contract)
            db_session.commit()

            return redirect(url_for('contrats'))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/<numContrat>', methods=['GET', 'POST'])
def contrats_by_num(numContrat):
    if request.method == 'GET': 
        contract = db_session.query(Contract).filter(Contract.id == numContrat).first()
        events = db_session.query(Event).filter(Event.idContrat == numContrat)
        documents = db_session.query(Document).filter(Document.idContrat == numContrat)

        return render_template('contrat_detail.html', contract = contract, events = events, documents = documents)
    elif request.method == 'POST' and request.form.get('_method') == 'PUT':
        contract = db_session.query(Contract).filter(Contract.id == numContrat).first()
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
        
        db_session.commit()

        return redirect(url_for('contrats'))

@app.route('/contrats/<numContrat>/evenement', methods=['POST'])
def add_contrats_event(numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST':
            #Récupération des données du formulaire*
            idContrat = request.form.get('idContratE')
            dateEvenement = request.form.get('dateEvenementE')
            Type = request.form.get('TypeE0')
            SType = request.form.get('STypeE0')
            Descriptif = request.form.get('DescriptifE')

            event = Event(idContrat = idContrat, dateEvenement = dateEvenement, Type = Type, SType = SType, Descriptif = Descriptif)
            
            db_session.add(event)
            db_session.commit()

            return redirect(url_for('contrats_by_num', numContrat=idContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/<numContrat>/document', methods=['POST'])
def add_contrats_document(numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST':
            #Récupération du dernier élément
            last_doc = db_session.query(Document).order_by(Document.id.desc()).first()
            if last_doc:
                id = last_doc.id + 1
            else:
                id = 1

            #Récupération des données du formulaire
            idContrat = request.form.get('idContratD')
            dateDocument = request.form.get('dateDocumentD')
            Type = request.form.get('TypeD0')
            SType = request.form.get('STypeD0')
            Descriptif = request.form.get('DescriptifD')
            DocumentBinaire = request.files['documentD']
            extention = os.path.splitext(DocumentBinaire.filename)[1]
            Name = docs.create_name(dateDocument, idContrat, id, SType)
            LienDocument = Name + extention

            #Création du document dans la base de données
            document = Document(idContrat = idContrat, Type = Type, SType = SType, Descriptif = Descriptif, strLien = LienDocument, dateDocument = dateDocument, Name = Name)
            
            #Ajout et Fermeture de la session
            db_session.add(document)
            db_session.commit()

            #Enregistrement du fichier sur le serveur
            docs.upload_file(DocumentBinaire, Name, extention)

            #Retour du formulaire
            return redirect(url_for('contrats_by_num', numContrat=idContrat))
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/numContrat/<numContrat>/numEvenement/<numEvent>', methods=['POST'])
def modif_event_id(numEvent, numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST' and request.form.get('_method') == 'PUT':
            #Récupération de l'évènement
            event = db_session.query(Event).filter(Event.id == numEvent).first()

            if event:
                #Récupération formulaire
                idContrat = request.form.get(f'idContratE{numEvent}')
                event.idContrat = request.form.get(f'idContratE{numEvent}')
                event.dateEvenement = request.form.get(f'dateEvenementE{numEvent}')
                event.Type = request.form.get(f'TypeE{numEvent}')
                event.SType = request.form.get(f'STypeE{numEvent}')
                event.Descriptif = request.form.get(f'DescriptifE{numEvent}')

                #Retour
                db_session.commit()

                return redirect(url_for('contrats_by_num', numContrat = idContrat))

    else:
        return redirect(url_for('logout'))

@app.route('/contrats/numContrat/<numContrat>/numDocument/<numDoc>', methods=['POST'])
def modif_document_id(numDoc, numContrat):
    if '2' in str(session['habilitation']):
        if request.method == 'POST' and request.form.get('_method') == 'PUT':
            #Récupération du document
            document = db_session.query(Document).filter(Document.id == numDoc).first()

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
                document.Descriptif = request.form.get(f'DescriptifD{numDoc}')
                if request.files[f'documentD{numDoc}']:
                    DocumentBinaire = request.files[f'documentD{numDoc}']
                    Name = docs.create_name(dateDocument, idContrat, id, SType)
                    extention = os.path.splitext(DocumentBinaire.filename)[1]
                else:
                    strLien = request.form.get(f'strLienD{numDoc}')
                    completName = strLien.split('_')[3]
                    Name = docs.create_name(dateDocument, idContrat, id, SType)
                    extention = completName.split('.')[1]
                LienDocument = Name + '.' + extention
                document.strLien = LienDocument

                # création d'un nom de document
                date_date = datetime.datetime.strptime(dateDocument, '%Y-%m-%d').date()
                str_date = date_date.strftime('%y%m%d')
                str_idContrat = str(idContrat).zfill(6)
                str_idDocument = str(id).zfill(6)
                str_SType = SType[:5]
                Name = f"{str_date}_{str_idContrat}_{str_idDocument}_{str_SType}"

                #Gestion automatique du nom de document
                document.Name = Name

                #Retour
                db_session.commit()

                return redirect(url_for('contrats_by_num', numContrat = idContrat))
            
    else:
        return redirect(url_for('logout'))

@app.route('/contrats/numContrat/<numContrat>/numDocument/<numDoc>/download/<Name>', methods=['GET'])
def download_document(numDoc, numContrat, Name:str):
    if '2' in str(session['habilitation']):
        extention = Name.split('.')[1]
        Name = Name.split('.')[0]
        return docs.download_file(file_name=Name, extension=extention)
    else:
        return redirect(url_for('logout'))
