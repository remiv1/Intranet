"""Module contenant la modélisation de données de l'application.

.. classes::
    - `User`: Représente un utilisateur dans la base de données.
    - `Contract`: Représente un contrat dans la base de données.
    - `Contacts`: Représente les contacts dans la base de données.
    - `Document`: Représente un document dans la base de données.
    - `Event`: Représente un événement dans la base de données.
    - `Bill`: Représente une facture dans la base de données.
    - `DocToSigne`: Représente un document à signer dans la base de données.
    - `Points`: Représente les points dans la base de données.
    - `Signatures`: Représente une signature dans la base de données.
    - `Invitation`: Représente une invitation dans la base de données.
    - `AuditLog`: Représente les journaux d'audit dans la base de données.
    - `ViewPoint`: Représente un point de vue dans la base de données.

.. constants::
    - `PK_CONTRACT`: Clé primaire de la table des contrats.
    - `PK_DOC_TO_SIGNE`: Clé primaire de la table des documents à signer.
    - `PK_USER`: Clé primaire de la table des utilisateurs.
    - `PK_POINTS`: Clé primaire de la table des points.
    - `CASCADE`: Stratégie de suppression en cascade pour les relations.
    - `Base`: Classe de base pour les modèles SQLAlchemy.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.2.0
"""
from ._common import Base
from .audit_db import AuditLog
from .auth_session import AuthSession
from .bill import Bill
from .contacts import Contacts
from .contract import Contract
from .doc_to_sign import DocToSigne
from .document import Document
from .event import Event
from .invitation import Invitation
from .points import Points
from .signature import Signatures
from .user import User
from .view_point import ViewPoints

__all__ = [
    "AuditLog",
    "AuthSession",
    "Base",
    "Bill",
    "Contacts",
    "Contract",
    "DocToSigne",
    "Document",
    "Event",
    "Invitation",
    "Points",
    "Signatures",
    "User",
    "ViewPoints",
]
