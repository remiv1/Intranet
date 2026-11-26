"""Coordonnées partagées entre le carnet et les contacts des contrats."""

from ..forms import ContactForm
from ..models import Contacts

CONTACT_FIELDS = {
    'nomC': 'nom',
    'fonctionC': 'fonction',
    'mailC': 'mail',
    'telFixeC': 'tel_fixe',
    'telPortableC': 'tel_portable',
    'adresseC': 'adresse',
    'codePostalC': 'code_postal',
    'villeC': 'ville',
}


def contact_form_data(contact: Contacts) -> dict[str, object]:
    """Prépare un formulaire à partir d'une fiche existante."""
    return {field: getattr(contact, attribute) for field, attribute in CONTACT_FIELDS.items()}


def update_contact(contact: Contacts, form: ContactForm) -> None:
    """Applique les coordonnées validées sans modifier les associations."""
    for field, attribute in CONTACT_FIELDS.items():
        value = getattr(form, field).data or ''
        setattr(contact, attribute, value.strip())
