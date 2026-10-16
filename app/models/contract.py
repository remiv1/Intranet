"""Module contenant la modélisation des contrats dans l'application.

.. classes::
    - `Contract`: Représente un contrat dans la base de données.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from datetime import date
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Integer, String, Date
from sqlalchemy.orm import mapped_column, relationship, Mapped

from ._common import Base, CASCADE

if TYPE_CHECKING:
    from . import Contacts, Event, Bill, Document


class Contract(Base):
    """Représente un contrat dans le système.

    :param id: Identifiant unique du contrat.
    :type id: int
    :param type_contrat: Type du contrat (Immobilier, Services, ...).
    :type type_contrat: str
    :param sous_type_contrat: Sous-type du contrat (Suivant dictionnaire des types et sous_type).
    :type sous_type_contrat: str
    :param entreprise: Nom de l'entreprise associée au contrat.
    :type entreprise: str
    :param id_externe_contrat: Identifiant externe du contrat (numéro de contrat).
    :type id_externe_contrat: str
    :param intitule: Intitulé du contrat.
    :type intitule: str
    :param date_debut: Date de début de validité du contrat.
    :type date_debut: date
    :param date_fin_preavis: Date de fin de préavis du contrat.
    :type date_fin_preavis: date
    :param date_fin: Date de fin de validité du contrat (optionnelle).
    :type date_fin: date

    .. table:: `01_contrats`

    .. relations::
        - `contacts` (List[Contacts]): Liste des contacts associés au contrat.
        - `evenements` (List[Event]): Liste des événements associés au contrat.
        - `factures` (List[Bill]): Liste des factures associées au contrat.
        - `documents` (List[Document]): Liste des documents associés au contrat.
    
    ..methodes::
        - `__repr__() -> str`: Retourne une représentation textuelle de l'objet Contract.

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    
    __tablename__ = '01_contrats'

    # Données principales
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique du contrat."
    )
    type_contrat: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type du contrat."
    )
    sous_type_contrat: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Sous-type du contrat."
    )
    entreprise: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Entreprise associée au contrat."
    )
    id_externe_contrat: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Identifiant externe du contrat (numéro de contrat)."
    )
    intitule: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Intitulé du contrat."
    )

    # Dates
    date_debut: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date de début du contrat."
    )
    date_fin_preavis: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date de fin de préavis du contrat."
    )
    date_fin: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date de fin du contrat."
    )

    # Relations
    contacts: Mapped[List["Contacts"]] = relationship(
        "Contacts",
        back_populates="contrat",
        cascade=CASCADE,
    )
    evenements: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="contrat",
        cascade=CASCADE,
    )
    factures: Mapped[List["Bill"]] = relationship(
        "Bill",
        back_populates="contrat",
        cascade=CASCADE,
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="contrat",
        cascade=CASCADE,
    )

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Contract.

        .. exemple::
            La commande suivante...
            .. code-block:: python
            print(contract)
            ...affiche la représentation suivante...
            .. code-block:: python
            >>> <Contract(id=1, type_contrat='Immobilier', sous_type_contrat='Bail commercial',
            entreprise='Entreprise XYZ', id_externe_contrat='C12345',
            intitule='Contrat de location bureau', date_debut=2024-01-01,
            date_fin_preavis=2024-12-31, date_fin=2025-12-31)>
        """
        return (
            f"<Contract(id={self.id}, type_contrat='{self.type_contrat}', "
            f"sous_type_contrat='{self.sous_type_contrat}', entreprise='{self.entreprise}', "
            f"id_externe_contrat='{self.id_externe_contrat}', intitule='{self.intitule}', "
            f"date_debut={self.date_debut}, date_fin_preavis={self.date_fin_preavis}, "
            f"date_fin={self.date_fin})>"
        )
