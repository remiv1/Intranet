"""Modèle représentant un contact associé à un contrat.

.. classes::
    - `Contacts` (Contacts): Représente un contact associé à un contrat.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. module_version:: 1.0.0
"""
from typing import Optional
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped
from ._common import Base, PK_CONTRACT

class Contacts(Base):
    """Représente un contact associé à un contrat.

    :param id: Identifiant unique du contact.
    :type id: int
    :param id_contrat: Identifiant du contrat associé.
    :type id_contrat: int
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
        - `contrat`: Le contrat associé à ce contact.

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
    id_contrat: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_CONTRACT),
        nullable=False,
        comment="Identifiant du contrat associé."
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
    contrat = relationship(
        "Contract",
        back_populates="contacts",
    )

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Contacts.
        
        .. exemple::
            .. code-block:: python
                print(contact)
                >>> <Contacts(id=1, id_contrat=1, nom='Doe', prenom='John', fonction='Manager',
                mail='john.doe@example.com', tel_fixe='0123456789', tel_portable='0612345678',
                adresse='123 Rue de Paris', code_postal='75001', ville='Paris', pays='France')>
            
        """
        return (
            f"<Contacts(id={self.id}, id_contrat={self.id_contrat}, nom='{self.nom}', "
            f"prenom='{self.prenom}', fonction='{self.fonction}', mail='{self.mail}', "
            f"tel_fixe='{self.tel_fixe}', tel_portable='{self.tel_portable}', "
            f"adresse='{self.adresse}', code_postal='{self.code_postal}', "
            f"ville='{self.ville}', pays='{self.pays}')>"
        )
