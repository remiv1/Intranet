"""Module contenant la modélisation des événements dans l'application.

.. classes::
    - `Event`: Représente un événement dans la base de données.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, Date, ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped

from ._common import Base, PK_CONTRACT

class Event(Base):
    """Représente un événement associé à un contrat.

    :param id: Identifiant unique de l'événement.
    :type id: int
    :param id_contrat: Identifiant du contrat associé.
    :type id_contrat: int
    :param type_evenement: Type de l'événement (Renouvellement, Résiliation, etc.).
    :type type_evenement: str
    :param sous_type_evenement: Sous-type de l'événement.
    :type sous_type_evenement: str
    :param date_evenement: Date de l'événement.
    :type date_evenement: date
    :param descriptif: Descriptif de l'événement.
    :type descriptif: str

    .. relations ::
        - `contrat` (Contract): Contrat associé à l'événement.

    .. table:: `12_evenements`

    .. methods ::
        - `__repr__()` -> str: Retourne une représentation textuelle de l'objet Event.
    
    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    __tablename__ = '12_evenements'

    # Données principales
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique de l'événement.",
    )
    id_contrat: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_CONTRACT),
        nullable=False,
        comment="Identifiant du contrat associé.",
    )
    type_evenement: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type de l'événement (Renouvellement, Résiliation, etc.).",
    )
    sous_type_evenement: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Sous-type de l'événement.",
    )
    date_evenement: Mapped[datetime] = mapped_column(
        Date,
        nullable=False,
        comment="Date de l'événement.",
    )
    descriptif: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Descriptif de l'événement.",
    )

    # Relations
    contrat = relationship(
        "Contract",
        back_populates="evenements",
    )

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Event.

        .. example::
            .. code-block:: python
            print(event)
            >>> <Event(id=1, id_contrat=1, date_evenement=2024-09-25,
            type_evenement='Renouvellement', sous_type_evenement='Annuel',
            descriptif='Renouvellement du contrat annuel')>
        """
        return (
            f"<Event(id={self.id}, id_contrat={self.id_contrat}, "
            f"date_evenement={self.date_evenement}, type_evenement='{self.type_evenement}', "
            f"sous_type_evenement='{self.sous_type_evenement}', descriptif='{self.descriptif}')>"
        )
