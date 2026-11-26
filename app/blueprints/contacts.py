"""Carnet de contacts indépendant des contrats, réservé aux gestionnaires."""

from flask import Blueprint, abort, g, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from ..forms import ContactBookForm, DeleteContactForm
from ..habilitations import GESTIONNAIRE, validate_habilitation
from ..models import Contacts, Contract
from ..repositories.contacts import contact_form_data, update_contact

contacts_bp = Blueprint('contacts', __name__, url_prefix='/ea/contacts')
CONTACTS_INDEX = 'contacts.index'


def _contracts() -> list[Contract]:
    return list(g.db_session.scalars(select(Contract).order_by(Contract.intitule, Contract.id)))


def _choices(contracts: list[Contract]) -> list[tuple[int, str]]:
    return [(contract.id, f'{contract.intitule} · {contract.entreprise} (n° {contract.id})')
            for contract in contracts]


@contacts_bp.get('')
@validate_habilitation(GESTIONNAIRE)
def index() -> ResponseReturnValue:
    """Affiche les fiches du carnet et leurs contrats associés."""
    query = request.args.get('q', '').strip()
    statement = select(Contacts).options(selectinload(Contacts.contrats))
    if query:
        pattern = '%' + query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        statement = statement.where(or_(Contacts.nom.ilike(pattern, escape='\\'),
                                       Contacts.mail.ilike(pattern, escape='\\')))
    contacts = list(g.db_session.scalars(statement.order_by(Contacts.nom, Contacts.id)))
    return render_template(
        'contacts.html', contacts=contacts, query=query,
        delete_forms={contact.id: DeleteContactForm(data={'contact_id': contact.id})
                      for contact in contacts},
        success_message=request.args.get('success_message'),
        error_message=request.args.get('error_message'),
    )


@contacts_bp.route('/nouveau', methods=['GET', 'POST'])
@validate_habilitation(GESTIONNAIRE)
def create() -> ResponseReturnValue:
    """Crée une fiche avec zéro ou plusieurs contrats."""
    return _edit(None)


@contacts_bp.route('/<int:contact_id>', methods=['GET', 'POST'])
@validate_habilitation(GESTIONNAIRE)
def edit(contact_id: int) -> ResponseReturnValue:
    """Modifie la fiche et sa sélection de contrats."""
    contact = g.db_session.get(Contacts, contact_id)
    if contact is None:
        abort(404)
    return _edit(contact)


def _edit(contact: Contacts | None) -> ResponseReturnValue:
    contracts = _contracts()
    values = contact_form_data(contact) if contact is not None else {}
    if contact is not None:
        values['contrats'] = [contract.id for contract in contact.contrats]
    form = ContactBookForm(data=values)
    form.contrats.choices = _choices(contracts)
    if request.method == 'POST' and form.validate_on_submit():
        selected = set(form.contrats.data or [])
        try:
            if contact is None:
                contact = Contacts()
                g.db_session.add(contact)
            update_contact(contact, form)
            contact.contrats = [contract for contract in contracts if contract.id in selected]
            g.db_session.commit()
            return redirect(url_for(CONTACTS_INDEX, success_message='Contact enregistré.'))
        except SQLAlchemyError:
            g.db_session.rollback()
            return render_template('contact_edit.html', contact=contact, form=form,
                                   error_message='Enregistrement du contact indisponible.'), 503
    return render_template('contact_edit.html', contact=contact, form=form), (
        400 if request.method == 'POST' else 200
    )


@contacts_bp.post('/<int:contact_id>/supprimer')
@validate_habilitation(GESTIONNAIRE)
def delete(contact_id: int) -> ResponseReturnValue:
    """Supprime la fiche et ses associations, jamais les contrats."""
    form = DeleteContactForm()
    if not form.validate_on_submit() or form.contact_id.data != str(contact_id):
        abort(400)
    contact = g.db_session.get(Contacts, contact_id)
    if contact is None:
        abort(404)
    try:
        g.db_session.delete(contact)
        g.db_session.commit()
    except SQLAlchemyError:
        g.db_session.rollback()
        return redirect(url_for(CONTACTS_INDEX, error_message='Suppression indisponible.'))
    return redirect(url_for(CONTACTS_INDEX, success_message='Fiche et associations supprimées.'))
