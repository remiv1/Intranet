"""Modèle représentant un contact du carnet administratif.

.. classes::
    - `Contacts` (Contacts): Représente un contact associé à un contrat.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. module_version:: 1.0.0
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import mapped_column, relationship, Mapped
from ._common import Base, PK_CONTRACT

if TYPE_CHECKING:
    from .contract import Contract

contacts_contrats = Table(
    '02_contacts_contrats',
    Base.metadata,
    Column('id_contact', Integer, ForeignKey('02_contacts.id', ondelete='CASCADE'),
           primary_key=True),
    Column('id_contrat', Integer, ForeignKey(PK_CONTRACT, ondelete='CASCADE'),
           primary_key=True, index=True),
)

class Contacts(Base):
    """Représente un contact indépendant associé à zéro ou plusieurs contrats.

    :param id: Identifiant unique du contact.
    :type id: int
    :param nom: Nom du contact.
    :type nom: str
    :param fonction: Fonction du contact.
    :type fonction: str
    :param mail: Adresse e-mail du contact.
    :type mail: str
    :param tel_fixe: Numéro de téléphone fixe du contact.
    :type tel_fixe: str
    :param tel_portable: Numéro de téléphone portable du contact.
    :type tel_portable: str
    :param adresse: Adresse postale du contact.
    :type adresse: str
    :param code_postal: Code postal du contact.
    :type code_postal: str
    :param ville: Ville du contact.
    :type ville: str

    .. relations::
        - `contrats`: Les contrats associés à ce contact.

    .. table:: `02_contacts`

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    __tablename__ = '02_contacts'

    # Données principales
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique du contact."
    )

    # Coordonnées
    nom: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nom du contact."
    )
    fonction: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Fonction du contact."
    )
    mail: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Adresse e-mail du contact."
    )
    tel_fixe: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Numéro de téléphone fixe du contact."
    )
    tel_portable: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Numéro de téléphone portable du contact."
    )
    adresse: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Adresse postale du contact."
    )
    code_postal: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Code postal du contact."
    )
    ville: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Ville du contact."
    )

    # Relations
    contrats: Mapped[list[Contract]] = relationship(
        "Contract",
        secondary=contacts_contrats,
        back_populates="contacts",
    )

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Contacts.
        
        .. exemple::
            .. code-block:: python
                print(contact)
                >>> <Contacts(id=1, nom='Doe', prenom='John', fonction='Manager',
                mail='john.doe@example.com', tel_fixe='0123456789', tel_portable='0612345678',
                adresse='123 Rue de Paris', code_postal='75001', ville='Paris', pays='France')>
            
        """
        return (
            f"<Contacts(id={self.id}, nom='{self.nom}', "
            f"fonction='{self.fonction}', mail='{self.mail}', "
            f"tel_fixe='{self.tel_fixe}', tel_portable='{self.tel_portable}', "
            f"adresse='{self.adresse}', code_postal='{self.code_postal}', "
            f"ville='{self.ville}')>"
        )
