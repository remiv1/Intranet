"""
==========================================================
Routes spécifiques aux contrats de l'Intranet API'Raudière
==========================================================
Fichier Blueprint des routes spécifiques aux contrats de l'Intranet API'Raudière.

Auteur : Rémi Verschuur

Date : 2025-09-11

Routes disponibles (prefixe '/contrats') :
- '/' : Accès à la liste des contrats (GET) et ajout d'un contrat (POST)
- '/contrat-<int:id_contrat>' : Détail d'un contrat (GET) et modification d'un contrat (POST)
- '/contrat-<int:id_contrat>/evenement' : Création d'un évènement d'un contrat (POST)
- '/contrat-<int:id_contrat>/document' : Création d'un document d'un contrat (POST)
- '/contrat-<int:id_contrat>/evenement-<int:id_evenement>' : Modification d'un évènement d'un contrat (POST)
- '/contrat-<int:id_contrat>/document-<int:id_document>' : Modification d'un document d'un contrat (POST)
- '/contrat-<int:id_contrat>/download/<name>' : Téléchargement d'un document enregistré sur le serveur (GET)
"""

from flask import Blueprint, render_template, request, g, redirect, url_for
from flask.typing import ResponseReturnValue
from utilities import (
    get_jsoned_datas, NOT_ALLOWED, JSON_MENUS, TYPINGS, ACCUEIL_CONTRAT, DETAIL_CONTRAT
    )
from models import Contract, Event, Document, Bill
from typing import Any
from habilitations import validate_habilitation, GESTIONNAIRE
from docs import download_file
from logging import getLogger

log = getLogger(__name__)

contracts_bp = Blueprint('contracts_bp', __name__, url_prefix='/contrats')

# Constantes et variables globales


@contracts_bp.route('/', methods=['GET', 'POST'])
@validate_habilitation(GESTIONNAIRE)
def contrats() -> ResponseReturnValue:
    """
    Route pour la gestion des contrats.
    Gère l'affichage et l'ajout de contrats.
    Args:
        None
    Returns:
        Response: La page de gestion des contrats ou une redirection vers la page de déconnexion
    """
    # === Gestion de la méthode GET (affichage de la liste des contrats) ===
    if request.method == 'GET':
        # Récupération des messages passés en paramètres GET
        message = request.args.get('message', None)
        success_message = request.args.get('success_message', None)
        error_message = request.args.get('error_message', None)

        # Récupération de la liste des contrats
        contracts = g.db_session.query(Contract).all()

        # Récupération des menus depuis le fichier JSON
        menus: str = get_jsoned_datas(file=JSON_MENUS,
                                      level_one=TYPINGS,
                                      level_two='Contrats',
                                      dumped=True)

        # Retourne la page de gestion des contrats et des messages éventuels
        return render_template('contrats.html', contracts=contracts, message=message,
                               success_message=success_message, error_message=error_message, menus_data=menus)

    # === Gestion de la méthode POST (ajout d'un nouveau contrat) ===
    elif request.method == 'POST':
        # Récupération des données du formulaire
        type_contrat = request.form.get('Type0', '')
        sous_type_contrat = request.form.get('SType0', '')
        entreprise = request.form.get('Entreprise', '')
        id_contrat_externe = request.form.get('numContratExterne', '')
        intitule = request.form.get('Intitule', '')
        date_debut = request.form.get('dateDebut', '')
        date_fin_preavis = request.form.get('dateFinPreavis', '')
        date_fin = request.form.get('dateFin', None)
        try:
            # Création et ajout du contrat à la base de données
            contract = Contract(type_contrat=type_contrat,
                                sous_type_contrat=sous_type_contrat,
                                entreprise=entreprise,
                                id_externe_contrat=id_contrat_externe,
                                intitule=intitule,
                                date_debut=date_debut,
                                date_fin=date_fin if date_fin else None,
                                date_fin_preavis=date_fin_preavis)
            g.db_session.add(contract)
            g.db_session.commit()

            # Message de succès et redirection
            message = f'Contrat ajouté avec succès : {contract.intitule}'
            return redirect(url_for(ACCUEIL_CONTRAT, success_message=message))
        except Exception as e:
            message = f'Erreur lors de l\'ajout du contrat {intitule} : {e}'
            return redirect(url_for(ACCUEIL_CONTRAT, error_message=message))
    else:
        return redirect(url_for(ACCUEIL_CONTRAT, error_message=NOT_ALLOWED))

@contracts_bp.route('/contrat-<int:id_contrat>', methods=['GET', 'POST'])
@validate_habilitation(GESTIONNAIRE)
def contrats_by_num(id_contrat: int) -> ResponseReturnValue:
    """
    Route pour le détail d'un contrat.
    Gère l'affichage, la modification et la suppression d'un contrat.
    Args:
        id_contrat (int): Le numéro du contrat à afficher/modifier/supprimer.
    Returns:
        Response: La page de détail du contrat ou une redirection vers la page de gestion des
    """
    tab = request.args.get('tab', 'e')
    # Récupération du contrat
    contract = g.db_session.query(Contract).filter(Contract.id == id_contrat).first()

    # === Gestion de la méthode GET (affichage du détail du contrat) ===
    if request.method == 'GET':
        # Récupération des messages passés en paramètres GET
        message = request.args.get('message', None)
        success_message = request.args.get('success_message', None)
        error_message = request.args.get('error_message', None)

        # Récupération du contrat, des évènements et des documents associés
        events = list(g.db_session.query(Event).filter(Event.id_contrat == id_contrat))
        documents = list(g.db_session.query(Document).filter(Document.id_contrat == id_contrat))
        bills = list(g.db_session.query(Bill).filter(Bill.id_contrat == id_contrat))

        # Récupération des filtres depuis le fichier JSON
        document_typing = get_jsoned_datas(file=JSON_MENUS, level_one=TYPINGS, level_two='Documents', dumped=False)
        event_typing = get_jsoned_datas(file=JSON_MENUS, level_one=TYPINGS, level_two='Evènements', dumped=False)

        # Affichage de la page de détail du contrat
        return render_template('contrat_detail.html', contract=contract, events=events, documents=documents, bills=bills,
                               message=message, success_message=success_message, error_message=error_message,
                               document_typing=document_typing, event_typing=event_typing, tab=tab)

    # === Gestion de la méthode POST (modification du contrat) ===
    elif request.method == 'POST' and request.form.get('_method') == 'PUT':
        # Récupération des données du formulaire
        type_contrat = request.form.get(f'Type{id_contrat}', '')
        sous_type_contrat = request.form.get(f'SType{id_contrat}', '')
        entreprise = request.form.get(f'Entreprise{id_contrat}', '')
        id_contrat_externe = request.form.get(f'numContratExterne{id_contrat}', '')
        intitule = request.form.get(f'Intitule{id_contrat}', '')
        date_debut = request.form.get(f'dateDebut{id_contrat}', '')
        date_fin_preavis = request.form.get(f'dateFinPreavis{id_contrat}', '')
        date_fin = request.form.get(f'dateFin{id_contrat}', None)

        try:
            if contract:
                # Modification des informations du contrat
                contract.type_contrat = type_contrat
                contract.sous_type_contrat = sous_type_contrat
                contract.entreprise = entreprise
                contract.id_externe_contrat = id_contrat_externe
                contract.intitule = intitule
                contract.date_debut = date_debut
                contract.date_fin_preavis = date_fin_preavis
                contract.date_fin = date_fin if date_fin != '' else None
                g.db_session.commit()

            # Message de succès et redirection
            message = f'Contrat {intitule} modifié avec succès'
            return redirect(url_for(ACCUEIL_CONTRAT, success_message=message))
        except Exception as e:
            # Message d'erreur et redirection
            message = f'Erreur lors de la modification du contrat {intitule} : {e}'
            return redirect(url_for(ACCUEIL_CONTRAT, error_message=message))

    # === Gestion de toute autre méthode ===
    else:
        return redirect(url_for(ACCUEIL_CONTRAT, error_message=NOT_ALLOWED))

@contracts_bp.route('/contrat-<int:id_contrat>/evenement', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def add_contrats_event(id_contrat: int) -> ResponseReturnValue:
    """
    Route pour l'ajout d'un évènement à un contrat.
    Gère l'ajout d'un évènement à un contrat dans la base de données.
    Args:
        id_contrat (int): Le numéro du contrat auquel ajouter l'évènement.
    Returns:
        Response: Redirection vers la page de détail du contrat.
    """
    tab = 'e'
    if request.method == 'POST':
        # Récupération des données du formulaire
        date_evenement = request.form.get('dateEvenementE')
        type_evenement = request.form.get('TypeE0')
        sous_type_evenement = request.form.get('STypeE0')
        descriptif = request.form.get('descriptifE')

        try:
            # Création de l'évènement dans la base de données
            event = Event(id_contrat = id_contrat,
                          date_evenement = date_evenement,
                          type_evenement = type_evenement,
                          sous_type_evenement = sous_type_evenement,
                          descriptif = descriptif)
            
            # Ajout commit de la session
            g.db_session.add(event)
            g.db_session.commit()

            # Message de succès et redirection
            message = f'Évènement {event.id} ajouté avec succès'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat=id_contrat, success_message=message, tab=tab))
        except Exception as e:
            # Message d'erreur et redirection
            message = f'Erreur lors de l\'ajout de l\'évènement : {e}'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=message, tab=tab))
    else:
        return redirect(url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=NOT_ALLOWED, tab=tab))

@contracts_bp.route('/contrat-<int:id_contrat>/document', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def add_contrats_document(id_contrat: int) -> ResponseReturnValue:
    """
    Route pour l'ajout d'un document à un contrat.
    Gère l'ajout d'un document à un contrat dans la base de données.
    Args:
        id_contrat (int): Le numéro du contrat auquel ajouter le document.
    Returns:
        Response: Redirection vers la page de détail du contrat.
    """
    # === Gestion de la méthode POST (ajout d'un nouveau document) ===
    tab = 'd'
    if request.method == 'POST':
        # Récupération des données du formulaire
        date_document = request.form.get('dateDocumentD', '')
        type_document = request.form.get('TypeD0', '')
        sous_type_document = request.form.get('STypeD0', '')
        descriptif = request.form.get('descriptifD', '')
        binary_file: Any = request.files.get('documentD', None)
        try:
            # Création du document dans la base de données
            document = Document(id_contrat = id_contrat, date_document = date_document,
                                type_document = type_document, sous_type_document = sous_type_document,
                                descriptif = descriptif)
            g.db_session.add(document)
            g.db_session.flush()  # Pour obtenir l'ID avant le commit
            document.create_name(binary_file=binary_file)
            document.upload(binary_file)

            # Ajout et Fermeture de la session
            g.db_session.commit()

            # Retour du formulaire
            message = f'Document {document.str_lien} ajouté avec succès'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat=id_contrat, success_message=message, tab=tab))
        except Exception as e:
            message = f'Erreur lors de l\'ajout du document {descriptif} : {e}'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=message, tab=tab))
    else:
        return redirect(url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=NOT_ALLOWED, tab=tab))

@contracts_bp.route('/contrat-<int:id_contrat>/facture', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def add_contrats_bill(id_contrat: int) -> ResponseReturnValue:
    """
    Route pour l'ajout d'une facture à un contrat.
    Gère l'ajout d'une facture à un contrat dans la base de données.
    Args:
        id_contrat (int): Le numéro du contrat auquel ajouter la facture.
    Returns:
        Response: Redirection vers la page de détail du contrat.
    """
    tab = 'f'
    if request.method == 'POST':

        # Récupération des données du formulaire
        date_facture = request.form.get('dateFactureF0', '')
        titre_facture = request.form.get('titreFactureF0', '')
        montant = request.form.get('montantFactureF0', '')
        binary_file: Any = request.files.get('documentF0', None)

        try:
            # Création de la facture dans la base de données
            bill = Bill(id_contrat=id_contrat,
                        date_facture=date_facture,
                        titre_facture=titre_facture,
                        montant=montant)
            g.db_session.add(bill)
            g.db_session.flush()  # Pour obtenir l'ID avant le commit
            bill.create_name(binary_file=binary_file)

            # Ajout et Fermeture de la session
            g.db_session.commit()

            # Enregistrement du fichier sur le serveur
            bill.upload(binary_file)

            # Retour du formulaire
            message = f'Facture {bill.titre_facture} ajoutée avec succès'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat=id_contrat, success_message=message, tab=tab))
        except Exception as e:
            message = f'Erreur lors de l\'ajout de la facture {titre_facture} : {e}'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=message, tab=tab))
    else:
        return redirect(url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=NOT_ALLOWED, tab=tab))

@contracts_bp.route('/contrat-<int:id_contrat>/evenement-<int:id_event>', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def modif_event_id(id_event: int, id_contrat: int) -> ResponseReturnValue:
    """
    Route pour la modification d'un évènement d'un contrat.
    Gère la modification d'un évènement d'un contrat dans la base de données.
    Args:
        id_event (int): Le numéro de l'évènement à modifier.
        id_contrat (int): Le numéro du contrat auquel l'évènement appartient.
    Returns:
        Response: Redirection vers la page de détail du contrat.
    """
    tab = 'e'
    # === Gestion de la méthode POST (modification d'un évènement) ===
    if request.method == 'POST' and request.form.get('_method') == 'PUT':
        # Récupération du formulaire
        date_evenement = request.form.get(f'dateEvenementE{id_event}')
        type_evenement = request.form.get(f'TypeE{id_event}')
        sous_type_evenement = request.form.get(f'STypeE{id_event}')
        descriptif = request.form.get(f'descriptifE{id_event}')

        try:
            # Récupération de l'évènement
            event = g.db_session.query(Event).filter(Event.id == id_event).first()

            if event:
                # Mise à jour des informations de l'évènement
                event.id_contrat = id_contrat
                event.date_evenement = date_evenement
                event.type_evenement = type_evenement
                event.sous_type_evenement = sous_type_evenement
                event.descriptif = descriptif

                # Retour
                g.db_session.commit()

                message = f'Évènement {event.id} modifié avec succès'
                return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, success_message=message, tab=tab))
            else:
                message = f'Évènement {id_event} non trouvé'
                return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab))
        except Exception:
            message = f'Erreur lors de la modification de l\'évènement {id_event}'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab))
    else:
        return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=NOT_ALLOWED, tab=tab))

@contracts_bp.route('/contrat-<int:id_contrat>/document-<int:id_document>', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def modif_document_id(id_document: int, id_contrat: int) -> ResponseReturnValue:
    """
    Route pour la modification d'un document d'un contrat.
    Gère la modification d'un document d'un contrat dans la base de données.
    Args:
        id_document (int): Le numéro du document à modifier.
        id_contrat (int): Le numéro du contrat auquel le document appartient.
    Returns:
        Response: Redirection vers la page de détail du contrat.
    """
    tab = 'd'
    new_binary_file: Any = request.files.get(f'documentD{id_document}', None)

    # === Gestion de la méthode POST (modification d'un document) ===
    if request.method == 'POST' and request.form.get('_method') == 'PUT':
        try:
            # Récupération du document
            document: Document = g.db_session.query(Document).filter(Document.id == id_document).first()

            # Récupération des anciennes valeurs pour conversion du fichier
            old_str_lien = document.str_lien or ''

            # Mise à jour des valeurs du document
            document.date_document = request.form.get(f'dateDocumentD{id_document}', '')
            document.type_document = request.form.get(f'TypeD{id_document}', '')
            document.sous_type_document = request.form.get(f'STypeD{id_document}', '')
            document.descriptif = request.form.get(f'descriptifD{id_document}', '')
            binary_changes = True if new_binary_file and new_binary_file.filename != '' else False
            if binary_changes:
                document.switch(file_to_switch=new_binary_file, old_file_name=old_str_lien)
            else:
                document.rename_file()

            # Enregistrement en base de données
            g.db_session.commit()

            # Message de succès et redirection
            message = f'Document {document.str_lien} modifié avec succès'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, success_message=message, tab=tab))

        except Exception as e:
            # Message d'erreur et redirection
            message = f'Erreur lors de la modification du document {id_document} : {e}'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab))
    else:
        return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=NOT_ALLOWED, tab=tab))

@contracts_bp.route('contrat-<int:id_contrat>/facture-<int:id_bill>', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def modif_bill_id(id_bill: int, id_contrat: int) -> ResponseReturnValue:
    """
    Route pour la modification d'une facture.
    Gère la modification d'une facture d'un contrat dans la base de données.
    Args:
        id_bill (int): Le numéro de la facture à modifier.
        id_contrat (int): Le numéro du contrat auquel la facture appartient.
    Returns:
        Response: Redirection vers la page de détail du contrat.
    """
    tab = 'f'
    new_binary_file: Any = request.files.get(f'fileFactureF{id_bill}', None)

    # === Gestion de la méthode POST (modification d'une facture) ===
    if request.method == 'POST' and request.form.get('_method') == 'PUT':

        try:
            # Récupération de la facture
            bill: Bill = g.db_session.query(Bill).filter(Bill.id == id_bill).first()

            # Récupération des anciennes valeurs pour conversion du fichier
            old_str_lien = bill.str_lien or ''

            # Mise à jour des valeurs de la facture
            bill.date_facture = request.form.get(f'dateFactureF{id_bill}', '')
            bill.titre_facture = request.form.get(f'titreFactureF{id_bill}', '')
            bill.montant = request.form.get(f'montantFactureF{id_bill}', '')
            binary_changes = True if new_binary_file and new_binary_file.filename != '' else False
            if binary_changes:
                bill.switch(file_to_switch=new_binary_file, old_file_name=old_str_lien)
            else:
                bill.rename_file()

            # Enregistrement en base de données
            g.db_session.commit()

            # Message de succès et redirection
            message = f'Facture {bill.titre_facture} modifiée avec succès'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, success_message=message, tab=tab))
        except Exception as e:
            message = f'Erreur lors de la modification de la facture {id_bill} : {e}'
            return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab))
    else:
        return redirect(url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=NOT_ALLOWED, tab=tab))

@contracts_bp.route('/download/<name>', methods=['GET'])
@validate_habilitation(GESTIONNAIRE)
def download_document(name: str) -> Any:
    """
    Route pour le téléchargement d'un document.
    Gère le téléchargement d'un document depuis le serveur.
    """
    return download_file(file_name_with_ext=name)
