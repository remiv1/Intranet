"""Formulaires de l'application."""

from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """Formulaire de connexion avec protection CSRF."""

    username = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])
    preview_request = HiddenField()
