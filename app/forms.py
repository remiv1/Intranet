"""Formulaires de l'application."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FileField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """Formulaire de connexion avec protection CSRF."""

    username = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])
    preview_request = HiddenField()


class ContractForm(FlaskForm):
    """Champs de création et de modification d'un contrat."""

    Type0 = SelectField(choices=[('', '')])
    SType0 = SelectField(choices=[('', '')])
    Entreprise = StringField()
    numContratExterne = StringField()
    Intitule = StringField()
    dateDebut = StringField(render_kw={'type': 'date'})
    dateFinPreavis = StringField(render_kw={'type': 'date'})
    dateFin = StringField(render_kw={'type': 'date'})


class ContactForm(FlaskForm):
    """Champs de création et de modification d'un contact."""

    nomC = StringField()
    fonctionC = StringField()
    mailC = StringField(render_kw={'type': 'email'})
    telFixeC = StringField(render_kw={'type': 'tel'})
    telPortableC = StringField(render_kw={'type': 'tel'})
    adresseC = StringField()
    codePostalC = StringField()
    villeC = StringField()


class DeleteContactForm(FlaskForm):
    """Champ cible d'une suppression de contact."""

    contact_id = HiddenField()


class EventForm(FlaskForm):
    """Champs de création et de modification d'un événement."""

    dateEvenementE = StringField(render_kw={'type': 'date'})
    TypeE0 = SelectField(choices=[('', '')])
    STypeE0 = SelectField(choices=[('', '')])
    descriptifE = TextAreaField()


class DocumentForm(FlaskForm):
    """Champs de création et de modification d'un document de contrat."""

    dateDocumentD = StringField(render_kw={'type': 'date'})
    TypeD0 = SelectField(choices=[('', '')])
    STypeD0 = SelectField(choices=[('', '')])
    descriptifD = TextAreaField()
    LienDocumentD = StringField()
    strLienD = HiddenField()
    documentD = FileField()


class BillForm(FlaskForm):
    """Champs de création et de modification d'une facture."""

    dateFactureF0 = StringField(render_kw={'type': 'date'})
    titreFactureF0 = StringField()
    montantFactureF0 = StringField(render_kw={'type': 'number', 'step': '0.01'})
    documentF0 = FileField()


class UserFieldsForm(FlaskForm):
    """Champs partagés de gestion des utilisateurs et habilitations."""

    prenom = StringField()
    nom = StringField()
    mail = StringField(render_kw={'type': 'email'})
    identifiant = StringField()
    mdp = PasswordField()
    habil1 = BooleanField(render_kw={'value': '1'})
    habil2 = BooleanField(render_kw={'value': '2'})
    habil3 = BooleanField(render_kw={'value': '3'})
    habil4 = BooleanField(render_kw={'value': '4'})
    habil5 = BooleanField(render_kw={'value': '5'})
    habil6 = BooleanField(render_kw={'value': '6'})


class UserCreateForm(UserFieldsForm):
    """Champs de création d'un utilisateur."""


class UserUpdateForm(UserFieldsForm):
    """Champs de modification d'un utilisateur, déverrouillage compris."""

    unlock = BooleanField(render_kw={'value': '1'})


class UserDeleteForm(FlaskForm):
    """Champ d'identification du compte à supprimer."""

    identifiant = StringField()


class UserRightsForm(FlaskForm):
    """Champs de modification des habilitations et du mot de passe."""

    identifiant = HiddenField()
    mdp = PasswordField()
    habil1 = BooleanField(render_kw={'value': '1'})
    habil2 = BooleanField(render_kw={'value': '2'})
    habil3 = BooleanField(render_kw={'value': '3'})
    habil4 = BooleanField(render_kw={'value': '4'})
    habil5 = BooleanField(render_kw={'value': '5'})
    habil6 = BooleanField(render_kw={'value': '6'})


class PrintDocumentForm(FlaskForm):
    """Champs d'impression et document envoyé à l'imprimante."""

    format = SelectField(choices=[('A5', 'A5'), ('A4', 'A4'), ('A3', 'A3')], default='A4')
    recto_verso = SelectField(choices=[
        ('one-sided', 'Recto seulement'),
        ('two-sided-short-edge', 'Recto-verso / Cote court'),
        ('two-sided-long-edge', 'Recto-verso / Cote long'),
    ], default='two-sided-long-edge')
    orientation = SelectField(choices=[('3', 'Portrait'), ('4', 'Paysage')], default='3')
    couleur = SelectField(choices=[('monochrome', 'Noir et blanc'), ('color', 'Couleur')])
    copies = IntegerField(default=1, render_kw={'min': '1', 'max': '100'})
    document = FileField()


class SignatureUploadForm(FlaskForm):
    """Champ du PDF déposé pour préparer une signature."""

    pdf = FileField()
    temp_dir = HiddenField(default='True')


class SignatureMakeForm(FlaskForm):
    """Champs transmis lors de la création d'un document à signer."""

    doc_id = HiddenField()
    document_name = HiddenField()
    document_type = HiddenField()
    document_subtype = HiddenField()
    document_priority = HiddenField()
    signing_deadline = HiddenField()
    document_validity = HiddenField()
    document_description = HiddenField()
