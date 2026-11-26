"""Module contenant la modélisation des signatures dans l'application.

.. classes::
    - `Signatures`: Représente les signatures apposées sur les points de signature.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from typing import Dict, Any

from sqlalchemy import Integer, DateTime, String, Text, func
from sqlalchemy.orm import mapped_column, relationship, Mapped

from ._common import Base

class Signatures(Base):
    """Représente une signature apposée sur un document.

    :param id: Identifiant unique de la signature.
    :type id: int
    :param signe_at: Date et heure de la signature.
    :type signe_at: datetime
    :param signature_hash: Hash de la signature pour vérification.
    :type signature_hash: str
    :param ip_addresse: Adresse IP de l'utilisateur au moment de la signature.
    :type ip_addresse: str
    :param user_agent: User-Agent du navigateur au moment de la signature.
    :type user_agent: str
    :param status: Statut de la signature (0: en attente, 1: signé, -1: annulé, -2: expiré).
    :type status: int
    :param svg_graph: Données SVG de la signature graphique (optionnel).
    :type svg_graph: str
    :param data_graph: Données JSON des coordonnées de la signature graphique (optionnel).
    :type data_graph: str
    :param largeur_graph: Largeur de la zone de signature graphique (optionnel).
    :type largeur_graph: int
    :param hauteur_graph: Hauteur de la zone de signature graphique (optionnel).
    :type hauteur_graph: int
    :param timestamp_graph: Horodatage de la signature graphique (optionnel).
    :type timestamp_graph: datetime

    .. relations::
        - `document (DocToSigne)`: Document associé à la signature.
        - `points (List[Points])`: Liste des points de signature associés à cette signature.
        - `user (User)`: Utilisateur ayant signé.

    .. table:: `22_signatures`

    .. methods::
        - `__repr__() -> str`: Représentation textuelle de l'objet Signatures.

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    __tablename__ = '22_signatures'

    # Données principales
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique de la signature."
    )

    # Données de signature
    signe_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=func.now(),    # pylint: disable=E1102
        comment="Horodatage de la signature."
    )
    signature_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Hash de la signature."
    )
    ip_addresse: Mapped[str] = mapped_column(
        String(45),
        nullable=True,
        comment="Adresse IP de l'utilisateur au moment de la signature."
    )
    user_agent: Mapped[str] = mapped_column(
        String(1024),
        nullable=True,
        comment="User agent de l'utilisateur au moment de la signature."
    )
    status: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Statut de la signature. 0: en attente, 1: signé, -1: annulé, -2: expiré"
    )

    # Signature graphique - AJOUT
    svg_graph: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Format SVG de la signature tracée."
    )
    data_graph: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Coordonnées JSON de la signature graphique (alternatif/backup)."
    )
    largeur_graph: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        comment="Largeur de la zone de signature graphique."
    )
    hauteur_graph: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        comment="Hauteur de la zone de signature graphique."
    )
    timestamp_graph: Mapped[DateTime] = mapped_column(
        DateTime,
        default=func.now(), # pylint: disable=E1102
        comment="Horodatage de la signature graphique."
    )

    # Relations
    points = relationship(
        "Points",
        back_populates="signature",
    )

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet Signatures.

        .. example::
            .. code-block:: python
            print(signature)
            >>> <Signatures(id=1, id_user=3, signe_at=2024-09-25 14:30:00, statut=1)>
        """
        return (f"<Signatures(id={self.id}, id_user={self.id_user}, signe_at={self.signe_at}, "
            f"status={self.status})>")

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet Signatures en dictionnaire. Utile pour la sérialisation JSON.

        :return: Dictionnaire représentant l'objet Signatures.
        :rtype: Dict[str, Any]

        .. example::
            .. code-block:: python
                signature_dict = signature.to_dict()
        """
        signature: Dict[str, Any] = {
            "id": self.id,
            "signe_at": self.signe_at.isoformat() if self.signe_at else None,   # type: ignore
            "signature_hash": self.signature_hash,
            "ip_addresse": self.ip_addresse,
            "user_agent": self.user_agent,
            "status": self.status,
            "svg_graph": self.svg_graph,
            "data_graph": self.data_graph,
            "largeur_graph": self.largeur_graph,
            "hauteur_graph": self.hauteur_graph,
            "timestamp_graph": (
                self.timestamp_graph.isoformat()  # type: ignore
                if self.timestamp_graph
                else None
            )
        }
        return signature
