"""Module contenant la modélisation des points de signature dans l'application.

.. classes::
    - `Points`: Représente les points de signature dans la base de données.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.2.0
"""
from __future__ import annotations

from typing import Dict, Any
from datetime import datetime

from sqlalchemy import Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import mapped_column, relationship, Mapped

from ._common import Base, PK_DOC_TO_SIGNE, PK_USER

class Points(Base):
    """Représente un point de signature sur un document PDF.

    :param id: Identifiant unique du point de signature.
    :type id: int
    :param id_document: Identifiant du document associé.
    :type id_document: int
    :param x: Position X en pixels (1/72 inch).
    :type x: Decimal
    :param y: Position Y en pixels (1/72 inch).
    :type y: Decimal
    :param page_num: Numéro de page (1-indexed).
    :type page_num: int
    :param id_user: Identifiant de l'utilisateur signataire.
    :type id_user: int
    :param status: Statut du point de signature (-2: annulé, -1: expiré, 0: en attente, 1: signé).
    :type status: int
    :param signe_at: Date et heure de la signature (si signée).
    :type signe_at: datetime

    .. relations::
        - `document (DocToSigne)`: Document associé au point de signature.
        - `user (User)`: Utilisateur signataire.
        - `signature (Signatures)`: Signature apposée sur ce point (si signée).

    .. table:: `21_points`

    .. methods::
        `__repr__() -> str`: Représentation textuelle de l'objet Points.
        `to_dict() -> Dict[str, Any]`: Convertit l'objet Points en dictionnaire.

    .. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    __tablename__ = '21_points'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique du point de signature."
    )
    id_document: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_DOC_TO_SIGNE),
        nullable=False,
        comment="Identifiant du document associé."
    )

    # Position sur le PDF
    x: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Position X en pixels (1/72 inch)."
    )
    y: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Position Y en pixels (1/72 inch)."
    )
    page_num: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Numéro de page (1-indexed)."
    )

    # Signataire assigné
    id_user: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_USER),
        nullable=False,
        comment="Identifiant de l'utilisateur signataire."
    )

    # Statut
    status: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Statut du point de signature (-2: annulé, -1: expiré, 0: en attente, 1: signé)."
    )
    id_signature: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('22_signatures.id'),
        nullable=True,
        comment="Identifiant de la signature apposée sur ce point (si signée)."
    )
    signe_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Date et heure de la signature (si signée)."
    )

    # Relations
    document = relationship(
        "DocToSigne",
        back_populates="points",
    )
    user = relationship(
        "User",
        back_populates="points",
    )
    signature = relationship(
        "Signatures",
        back_populates="points",
        uselist=False,
    )

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Points.

        .. example::
            .. code-block:: python
            print(point)
            >>> <Points(id=1, id_document=5, page_num=2, coordonnées=(150.00, 300.00),
            id_user=3, status=0)>
        """
        return (f"<Points(id={self.id}, id_document={self.id_document}, page_num={self.page_num}, "
            f"coordonnées=({self.x}, {self.y}), id_user={self.id_user}, status={self.status})>")

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet Points en dictionnaire. Utile pour la sérialisation JSON.

        :return: Dictionnaire représentant l'objet Points.
        :rtype: Dict[str, Any]

        .. example::
            .. code-block:: python
                point_dict = point.to_dict()
        """
        point: Dict[str, Any] = {
            "id": self.id,
            "id_document": self.id_document,
            "x": float(self.x),
            "y": float(self.y),
            "page_num": self.page_num,
            "id_user": self.id_user,
            "status": self.status,
            "signe_at": self.signe_at.isoformat() if self.signe_at else None    # type: ignore
        }
        return point
