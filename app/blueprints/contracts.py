"""Fichier Blueprint des routes spécifiques aux contrats de l'Intranet API'Raudière.

.. prefix:: `/contrats`

.. routes::
    - `/` : Accès à la liste des contrats (GET) et ajout d'un contrat (POST)
    - `/contrat-<int:id_contrat>` : Détail d'un contrat (GET) et modification d'un contrat (POST)
    - `/contrat-<int:id_contrat>/evenement` : Création d'un évènement d'un contrat (POST)
    - `/contrat-<int:id_contrat>/document` : Création d'un document d'un contrat (POST)
    - `/contrat-<int:id_contrat>/evenement-<int:id_evenement>` : Modif d'un évènement contrat (POST)
    - `/contrat-<int:id_contrat>/document-<int:id_document>` : Modif d'un doc d'un contrat (POST)
    - `/contrat-<int:id_contrat>/download/<name>` : Téléchargement d'un document (GET)

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.2.0
.. date:: 2025-09-11
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import Blueprint, render_template, request, g, redirect, url_for
from flask.typing import ResponseReturnValue
from sqlalchemy.exc import SQLAlchemyError

from ..utilities import (
    get_jsoned_datas,
    NOT_ALLOWED,
    JSON_MENUS,
    TYPINGS,
    ACCUEIL_CONTRAT,
    DETAIL_CONTRAT,
    )
from ..models import Contract, Contacts, Event, Document, Bill
from ..habilitations import validate_habilitation, GESTIONNAIRE
from ..docs import download_file, preserve_files_on_error
from ..forms import (
    BillForm,
    ContactForm,
    ContractForm,
    DeleteContactForm,
    DocumentForm,
    EventForm,
)

contracts_bp = Blueprint(
    'contracts_bp',
    __name__,
    url_prefix='/contrats',
)


@contracts_bp.route('/', methods=['GET', 'POST'])
@validate_habilitation(GESTIONNAIRE)
def contrats() -> ResponseReturnValue:
    """Route pour la gestion des contrats. Gère l'affichage et l'ajout de contrats.

    :return: La page de gestion des contrats ou une redirection vers la page de déconnexion
    :rtype: ResponseReturnValue
    """
    # === Gestion de la méthode GET (affichage de la liste des contrats) ===
    if request.method == 'GET':
        # Récupération des messages passés en paramètres GET
        message = request.args.get('message', None)
        success_message = request.args.get('success_message', None)
        error_message = request.args.get('error_message', None)

        # Récupération de la liste des contrats
        contracts = g.db_session.query(Contract).all()
        add_contract_form = ContractForm()
        add_contract_form.Type0.render_kw = {'data-contract-id': '0'}
        contract_forms = {
            contract.id: ContractForm(data={
                'Type0': contract.type_contrat,
                'SType0': contract.sous_type_contrat,
                'Entreprise': contract.entreprise,
                'numContratExterne': contract.id_externe_contrat,
                'Intitule': contract.intitule,
                'dateDebut': contract.date_debut,
                'dateFinPreavis': contract.date_fin_preavis,
                'dateFin': contract.date_fin,
            })
            for contract in contracts
        }
        for contract in contracts:
            contract_form = contract_forms[contract.id]
            contract_form.Type0.render_kw = {
                'data-contract-id': str(contract.id),
                'data-contract-value': contract.type_contrat,
            }
            contract_form.SType0.render_kw = {
                'data-contract-id': str(contract.id),
                'data-s-type-value': contract.sous_type_contrat,
            }

        # Récupération des menus depuis le fichier JSON
        menus: str = get_jsoned_datas(
            file=JSON_MENUS,
            level_one=TYPINGS,
            level_two='Contrats',
            dumped=True,
        )

        # Retourne la page de gestion des contrats et des messages éventuels
        return render_template(
            'contrats.html',
            contracts=contracts,
            message=message,
            success_message=success_message,
            error_message=error_message,
            menus_data=menus,
            add_contract_form=add_contract_form,
            contract_forms=contract_forms,
        )

    # === Gestion de la méthode POST (ajout d'un nouveau contrat) ===
    if request.method == 'POST':
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
            contract = Contract(
                type_contrat=type_contrat,
                sous_type_contrat=sous_type_contrat,
                entreprise=entreprise,
                id_externe_contrat=id_contrat_externe,
                intitule=intitule,
                date_debut=date_debut,
                date_fin=date_fin if date_fin else None,
                date_fin_preavis=date_fin_preavis,
            )
            g.db_session.add(contract)
            g.db_session.commit()

            # Message de succès et redirection
            message = f'Contrat ajouté avec succès : {contract.intitule}'
            return redirect(url_for(ACCUEIL_CONTRAT, success_message=message))
        except SQLAlchemyError as e:
            message = f'Erreur lors de l\'ajout du contrat {intitule} : {e}'
            return redirect(url_for(ACCUEIL_CONTRAT, error_message=message))
    return redirect(url_for(ACCUEIL_CONTRAT, error_message=NOT_ALLOWED))


@contracts_bp.route('/contrat-<int:id_contrat>', methods=['GET', 'POST'])
@validate_habilitation(GESTIONNAIRE)
def contrats_by_num(id_contrat: int) -> ResponseReturnValue:
    """Route pour le détail d'un contrat. Gère l'affichage, la modification et la suppression
    d'un contrat.

    :param id_contrat:: Le numéro du contrat à afficher/modifier/supprimer.
    :type id_contrat: int

    :return: La page de détail du contrat ou une redirection vers la page de gestion des contrats
    avec un message d'erreur ou de succès.
    :rtype: Response
    """
    tab = request.args.get('tab', 'c')
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
        contacts = list(g.db_session.query(Contacts).filter(Contacts.id_contrat == id_contrat))
        contact_forms = {
            contact.id: ContactForm(data={
                'nomC': contact.nom,
                'fonctionC': contact.fonction,
                'mailC': contact.mail,
                'telFixeC': contact.tel_fixe,
                'telPortableC': contact.tel_portable,
                'adresseC': contact.adresse,
                'codePostalC': contact.code_postal,
                'villeC': contact.ville,
            })
            for contact in contacts
        }
        contact_delete_forms = {
            contact.id: DeleteContactForm(data={'contact_id': contact.id})
            for contact in contacts
        }
        event_forms = {
            event.id: EventForm(data={
                'dateEvenementE': event.date_evenement,
                'TypeE0': event.type_evenement,
                'STypeE0': event.sous_type_evenement,
                'descriptifE': event.descriptif,
            })
            for event in events
        }
        event_form = EventForm()
        event_form.TypeE0.render_kw = {'data-event-id': '0', 'data-contract-id': '0'}
        event_form.descriptifE.render_kw = {'data-stype-event-value': ''}
        for event in events:
            current_form = event_forms[event.id]
            current_form.TypeE0.render_kw = {
                'data-event-id': str(event.id),
                'data-event-type-value': event.type_evenement,
                'data-contract-id': str(event.id_contrat),
            }
            current_form.STypeE0.render_kw = {
                'data-event-id': str(event.id),
                'data-stype-event-value': event.sous_type_evenement,
                'data-contract-id': str(event.id_contrat),
            }
        document_forms = {
            document.id: DocumentForm(data={
                'dateDocumentD': document.date_document,
                'TypeD0': document.type_document,
                'STypeD0': document.sous_type_document,
                'descriptifD': document.descriptif,
                'strLienD': document.str_lien,
            })
            for document in documents
        }
        document_form = DocumentForm()
        document_form.TypeD0.render_kw = {'data-document-id': '0', 'data-contract-id': '0'}
        document_form.STypeD0.render_kw = {'data-stype-document-value': ''}
        for document in documents:
            current_form = document_forms[document.id]
            current_form.TypeD0.render_kw = {
                'data-document-id': str(document.id),
                'data-document-type-value': document.type_document,
                'data-contract-id': str(document.id_contrat),
            }
            current_form.STypeD0.render_kw = {
                'data-stype-document-value': document.sous_type_document,
                'data-document-id': str(document.id),
            }
        bill_forms = {
            bill.id: BillForm(data={
                'dateFactureF0': bill.date_facture,
                'titreFactureF0': bill.titre_facture,
                'montantFactureF0': bill.montant,
            })
            for bill in bills
        }

        # Récupération des filtres depuis le fichier JSON
        document_typing = get_jsoned_datas(
            file=JSON_MENUS,
            level_one=TYPINGS,
            level_two='Documents',
            dumped=False,
        )
        event_typing = get_jsoned_datas(
            file=JSON_MENUS,
            level_one=TYPINGS,
            level_two='Evènements',
            dumped=False,
        )

        # Affichage de la page de détail du contrat
        return render_template(
            'contrat_detail.html',
            contract=contract,
            events=events,
            documents=documents,
            bills=bills,
            contacts=contacts,
            message=message,
            success_message=success_message,
            error_message=error_message,
            document_typing=document_typing,
            event_typing=event_typing,
            tab=tab,
            contact_form=ContactForm(),
            contact_forms=contact_forms,
            event_form=event_form,
            event_forms=event_forms,
            document_form=document_form,
            document_forms=document_forms,
            bill_form=BillForm(),
            bill_forms=bill_forms,
            contact_delete_forms=contact_delete_forms,
        )

    # === Gestion de la méthode POST (modification du contrat) ===
    if request.method == 'POST':
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
        except SQLAlchemyError as e:
            # Message d'erreur et redirection
            message = f'Erreur lors de la modification du contrat {intitule} : {e}'
            return redirect(url_for(ACCUEIL_CONTRAT, error_message=message))

    # === Gestion de toute autre méthode ===
    return redirect(url_for(ACCUEIL_CONTRAT, error_message=NOT_ALLOWED))


@contracts_bp.route('/contrat-<int:id_contrat>/contact', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def add_contrats_contact(id_contrat: int) -> ResponseReturnValue:
    """Route pour l'ajout d'un contact à un contrat. Gère l'ajout d'un contact à un contrat dans
    la base de données.

    :param id_contrat: Le numéro du contrat auquel ajouter le contact.
    :type id_contrat: int
    :returns: Response: Redirection vers la page de détail du contrat.
    :rtype: Response
    """
    tab = 'c'
    if request.method == 'POST':
        # Récupération des données du formulaire
        nom = request.form.get('nomC', '')
        fonction = request.form.get('fonctionC', '')
        mail = request.form.get('mailC', '')
        tel_fixe = request.form.get('telFixeC', '')
        tel_portable = request.form.get('telPortableC', '')
        adresse = request.form.get('adresseC', '')
        code_postal = request.form.get('codePostalC', '')
        ville = request.form.get('villeC', '')

        try:
            # Création du contact dans la base de données
            contact = Contacts(
                id_contrat=id_contrat,
                nom=nom,
                fonction=fonction,
                mail=mail,
                tel_fixe=tel_fixe,
                tel_portable=tel_portable,
                adresse=adresse,
                code_postal=code_postal,
                ville=ville,
            )

            # Ajout commit de la session
            g.db_session.add(contact)
            g.db_session.commit()

            # Message de succès et redirection
            message = f'Contact {contact.id} ajouté avec succès'
            return redirect(url_for(
                DETAIL_CONTRAT,
                id_contrat=id_contrat,
                success_message=message,
                tab=tab,
            ))
        except SQLAlchemyError as e:
            # Message d'erreur et redirection
            message = f'Erreur lors de l\'ajout du contact : {e}'
            return redirect(url_for(
                DETAIL_CONTRAT,
                id_contrat=id_contrat,
                error_message=message,
                tab=tab,
            ))
    return redirect(
        url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=NOT_ALLOWED, tab=tab)
    )


@contracts_bp.route('/contrat-<int:id_contrat>/evenement', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def add_contrats_event(id_contrat: int) -> ResponseReturnValue:
    """Route pour l'ajout d'un évènement à un contrat.Gère l'ajout d'un évènement à un contrat dans
    la base de données.

    :param id_contrat: Le numéro du contrat auquel ajouter l'évènement.
    :type id_contrat: int

    :return: Redirection vers la page de détail du contrat.
    :rtype: ResponseReturnValue
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
            event = Event(
                id_contrat = id_contrat,
                date_evenement = date_evenement,
                type_evenement = type_evenement,
                sous_type_evenement = sous_type_evenement,
                descriptif = descriptif,
            )

            # Ajout commit de la session
            g.db_session.add(event)
            g.db_session.commit()

            # Message de succès et redirection
            message = f'Évènement {event.id} ajouté avec succès'
            return redirect(url_for(
                DETAIL_CONTRAT, id_contrat=id_contrat, success_message=message, tab=tab
            ))
        except SQLAlchemyError as e:
            # Message d'erreur et redirection
            message = f'Erreur lors de l\'ajout de l\'évènement : {e}'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=message, tab=tab)
            )
    return redirect(
        url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=NOT_ALLOWED, tab=tab)
    )


@contracts_bp.route('/contrat-<int:id_contrat>/document', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def add_contrats_document(id_contrat: int) -> ResponseReturnValue:
    """Route pour l'ajout d'un document à un contrat. Gère l'ajout d'un document à un contrat dans
    la base de données.

    :param id_contrat: Le numéro du contrat auquel ajouter le document.
    :type id_contrat: int
    :returns: Redirection vers la page de détail du contrat.
    :rtype: ResponseReturnValue
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
            document = Document(
                id_contrat = id_contrat,
                date_document = date_document,
                type_document = type_document,
                sous_type_document = sous_type_document,
                descriptif = descriptif,
            )
            g.db_session.add(document)
            g.db_session.flush()  # Pour obtenir l'ID avant le commit
            if binary_file and binary_file.filename:
                document.create_name(binary_file=binary_file)
                with preserve_files_on_error(document.str_lien or ''):
                    document.upload(file_to_upload=binary_file)
                    g.db_session.commit()
            else:
                g.db_session.commit()

            # Retour du formulaire
            message = f'Document {document.str_lien} ajouté avec succès'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat=id_contrat, success_message=message, tab=tab)
            )
        except (OSError, SQLAlchemyError):
            g.db_session.rollback()
            raise
    return redirect(
        url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=NOT_ALLOWED, tab=tab)
    )


@contracts_bp.route('/contrat-<int:id_contrat>/facture', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def add_contrats_bill(id_contrat: int) -> ResponseReturnValue:
    """Route pour l'ajout d'une facture à un contrat. Gère l'ajout d'une facture à un contrat dans
    la base de données.

    :param id_contrat: Le numéro du contrat auquel ajouter la facture.
    :type id_contrat: int
    :returns: Redirection vers la page de détail du contrat.
    :rtype: ResponseReturnValue
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
            bill = Bill(
                id_contrat=id_contrat,
                date_facture=date_facture,
                titre_facture=titre_facture,
                montant=montant,
            )
            g.db_session.add(bill)
            g.db_session.flush()  # Pour obtenir l'ID avant le commit
            if binary_file and binary_file.filename:
                bill.create_name(binary_file=binary_file)
                with preserve_files_on_error(bill.str_lien or ''):
                    bill.upload(file_to_upload=binary_file)
                    g.db_session.commit()
            else:
                g.db_session.commit()

            # Retour du formulaire
            message = f'Facture {bill.titre_facture} ajoutée avec succès'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat=id_contrat, success_message=message, tab=tab)
            )
        except (OSError, SQLAlchemyError):
            g.db_session.rollback()
            raise
    return redirect(
        url_for(DETAIL_CONTRAT, id_contrat=id_contrat, error_message=NOT_ALLOWED, tab=tab)
    )


@contracts_bp.route('/contrat-<int:id_contrat>/contact-<int:id_contact>', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def modif_contact_id(id_contact: int, id_contrat: int) -> ResponseReturnValue:
    """Route pour la modification d'un contact d'un contrat. Gère la modification d'un contact d'un
    contrat dans la base de données.

    :param id_contact: Le numéro du contact à modifier.
    :type id_contact: int
    :param id_contrat: Le numéro du contrat auquel le contact appartient.
    :type id_contrat: int
    :returns: Redirection vers la page de détail du contrat.
    :rtype: ResponseReturnValue
    """
    tab = 'c'
    # === Gestion de la méthode POST (modification d'un contact) ===
    if request.method == 'POST':
        # Récupération du formulaire
        nom = request.form.get('nomC')
        fonction = request.form.get('fonctionC')
        mail = request.form.get('mailC')
        tel_fixe = request.form.get('telFixeC')
        tel_portable = request.form.get('telPortableC')
        adresse = request.form.get('adresseC')
        code_postal = request.form.get('codePostalC')
        ville = request.form.get('villeC')

        try:
            # Récupération du contact
            contact = g.db_session.query(Contacts).filter(Contacts.id == id_contact).first()

            if contact:
                # Mise à jour des informations du contact
                contact.id_contrat = id_contrat
                contact.nom = nom
                contact.fonction = fonction
                contact.mail = mail
                contact.tel_fixe = tel_fixe
                contact.tel_portable = tel_portable
                contact.adresse = adresse
                contact.code_postal = code_postal
                contact.ville = ville

                # Retour
                g.db_session.commit()

                message = f'Contact {contact.id} modifié avec succès'
                return redirect(url_for(
                        DETAIL_CONTRAT, id_contrat = id_contrat, success_message=message, tab=tab
                    ))
            message = f'Contact {id_contact} non trouvé'
            return redirect(
                url_for(
                    DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab
                )
            )
        except SQLAlchemyError:
            message = f'Erreur lors de la modification du contact {id_contact}'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab)
            )
    return redirect(
        url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=NOT_ALLOWED, tab=tab)
    )


@contracts_bp.route('/contrat-<int:id_contrat>/evenement-<int:id_event>', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def modif_event_id(id_event: int, id_contrat: int) -> ResponseReturnValue:
    """Route pour la modification d'un évènement d'un contrat. Gère la modification d'un évènement
    d'un contrat dans la base de données.

    :param id_event: Le numéro de l'évènement à modifier.
    :type id_event: int
    :param id_contrat: Le numéro du contrat auquel l'évènement appartient.
    :type id_contrat: int
    :returns: Redirection vers la page de détail du contrat.
    :rtype: ResponseReturnValue
    """
    tab = 'e'
    # === Gestion de la méthode POST (modification d'un évènement) ===
    if request.method == 'POST':
        # Récupération du formulaire
        date_evenement = request.form.get('dateEvenementE')
        type_evenement = request.form.get('TypeE0')
        sous_type_evenement = request.form.get('STypeE0')
        descriptif = request.form.get('descriptifE')

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
                return redirect(
                    url_for(
                        DETAIL_CONTRAT, id_contrat = id_contrat, success_message=message, tab=tab
                    )
                )
            message = f'Évènement {id_event} non trouvé'
            return redirect(
                url_for(
                    DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab
                )
            )
        except SQLAlchemyError:
            message = f'Erreur lors de la modification de l\'évènement {id_event}'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab)
            )
    return redirect(
        url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=NOT_ALLOWED, tab=tab)
    )


@contracts_bp.route('/contrat-<int:id_contrat>/document-<int:id_document>', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def modif_document_id(id_document: int, id_contrat: int) -> ResponseReturnValue:
    """Route pour la modification d'un document d'un contrat. Gère la modification d'un document
    d'un contrat dans la base de données.

    :param id_document: Le numéro du document à modifier.
    :type id_document: int
    :param id_contrat: Le numéro du contrat auquel le document appartient.
    :type id_contrat: int
    :returns: Redirection vers la page de détail du contrat.
    :rtype: ResponseReturnValue
    """
    tab = 'd'
    new_binary_file: Any = request.files.get('documentD', None)

    # === Gestion de la méthode POST (modification d'un document) ===
    if request.method == 'POST':
        try:
            # Récupération du document
            document: Document = g.db_session.query(Document) \
                .filter(Document.id == id_document) \
                .first()

            # Récupération des anciennes valeurs pour conversion du fichier
            old_str_lien = document.str_lien or ''

            # Mise à jour des valeurs du document
            document.date_document = datetime.strptime(
                request.form.get('dateDocumentD', ''),
                '%Y-%m-%d'
            )
            document.type_document = request.form.get('TypeD0', '')
            document.sous_type_document = request.form.get('STypeD0', '')
            document.descriptif = request.form.get('descriptifD', '')
            binary_changes = True if new_binary_file and new_binary_file.filename != '' else False
            if binary_changes:
                document.create_name(binary_file=new_binary_file)
            elif old_str_lien:
                document.create_name()
            new_str_lien = document.str_lien or ''
            with preserve_files_on_error(old_str_lien, new_str_lien):
                if binary_changes:
                    document.switch(file_to_switch=new_binary_file, old_file_name=old_str_lien)
                elif old_str_lien:
                    document.rename_file()
                g.db_session.commit()

            # Message de succès et redirection
            message = f'Document {document.str_lien} modifié avec succès'
            return redirect(
                url_for(
                    DETAIL_CONTRAT, id_contrat = id_contrat, success_message=message, tab=tab
                )
            )
        except ValueError as e:
            g.db_session.rollback()
            # Message d'erreur et redirection en cas de problème de conversion de date
            message = f'Erreur liée à la date. Modification document {id_document} impossible : {e}'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab)
            )

        except (OSError, SQLAlchemyError):
            g.db_session.rollback()
            raise
    else:
        return redirect(
            url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=NOT_ALLOWED, tab=tab)
        )


@contracts_bp.route('contrat-<int:id_contrat>/facture-<int:id_bill>', methods=['POST'])
@validate_habilitation(GESTIONNAIRE)
def modif_bill_id(id_bill: int, id_contrat: int) -> ResponseReturnValue:
    """Route pour la modification d'une facture. Gère la modification d'une facture d'un contrat
    dans la base de données.

    :param id_bill: Le numéro de la facture à modifier.
    :type id_bill: int
    :param id_contrat: Le numéro du contrat auquel la facture appartient.
    :type id_contrat: int

    :return: Redirection vers la page de détail du contrat.
    :rtype: ResponseReturnValue
    """
    tab = 'f'
    new_binary_file: Any = request.files.get('documentF0', None)

    # === Gestion de la méthode POST (modification d'une facture) ===
    if request.method == 'POST':

        try:
            # Récupération de la facture
            bill: Bill = g.db_session.query(Bill).filter(Bill.id == id_bill).first()

            # Récupération des anciennes valeurs pour conversion du fichier
            old_str_lien = bill.str_lien or ''

            # Mise à jour des valeurs de la facture
            bill.date_facture = datetime.strptime(
                request.form.get('dateFactureF0', ''),
                '%Y-%m-%d',
            )
            bill.titre_facture = request.form.get('titreFactureF0', '')
            bill.montant = int(request.form.get('montantFactureF0', ''))
            binary_changes = True if new_binary_file and new_binary_file.filename != '' else False
            if binary_changes:
                bill.create_name(binary_file=new_binary_file)
            elif old_str_lien:
                bill.create_name()
            new_str_lien = bill.str_lien or ''
            with preserve_files_on_error(old_str_lien, new_str_lien):
                if binary_changes:
                    bill.switch(file_to_switch=new_binary_file, old_file_name=old_str_lien)
                elif old_str_lien:
                    bill.rename_file()
                g.db_session.commit()

            # Message de succès et redirection
            message = f'Facture {bill.titre_facture} modifiée avec succès'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat = id_contrat, success_message=message, tab=tab)
            )

        except ValueError as e:
            g.db_session.rollback()
            message = f'Erreur lors de la modification de la facture {id_bill} : {e}'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab)
            )
        except (OSError, SQLAlchemyError):
            g.db_session.rollback()
            raise
    return redirect(
        url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=NOT_ALLOWED, tab=tab)
    )


@contracts_bp.route(
        '/contrat-<int:id_contrat>/contact-<int:id_contact>/supprimer',
        methods=['POST']
    )
@validate_habilitation(GESTIONNAIRE)
def delete_contact_id(id_contact: int, id_contrat: int) -> ResponseReturnValue:
    """
    Route pour la suppression d'un contact d'un contrat.
    Gère la suppression d'un contact d'un contrat dans la base de données.
    Args:
        id_contact (int): Le numéro du contact à supprimer.
        id_contrat (int): Le numéro du contrat auquel le contact appartient.
    Returns:
        Response: Redirection vers la page de détail du contrat.
    """
    tab = 'c'
    if request.method == 'POST':
        try:
            # Récupération du contact
            contact = g.db_session.query(Contacts).filter(Contacts.id == id_contact).first()

            if contact:
                # Suppression du contact
                g.db_session.delete(contact)
                g.db_session.commit()

                message = f'Contact {contact.id} supprimé avec succès'
                return redirect(
                    url_for(
                        DETAIL_CONTRAT, id_contrat = id_contrat, success_message=message, tab=tab
                    )
                )
            message = f'Contact {id_contact} non trouvé'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab)
            )
        except SQLAlchemyError as e:
            message = f'Erreur lors de la suppression du contact {id_contact} : {e}'
            return redirect(
                url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=message, tab=tab)
            )
    return redirect(
        url_for(DETAIL_CONTRAT, id_contrat = id_contrat, error_message=NOT_ALLOWED, tab=tab)
    )


@contracts_bp.route('/download/<name>', methods=['GET'])
@validate_habilitation(GESTIONNAIRE)
def download_document(name: str) -> Any:
    """
    Route pour le téléchargement d'un document.
    Gère le téléchargement d'un document depuis le serveur.
    """
    return download_file(file_name_with_ext=name)
