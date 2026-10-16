"""Modèles de documents à signer.

.. classes::
    -`DocToSign`:Modèle représentant un document à signer.

..module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
..version:: 1.0.0
"""
from __future__ import annotations

from datetime import datetime
import io
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Computed
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.sql import func

from ._common import Base, PK_USER, CASCADE

class DocToSigne(Base):
    """Représente un document à signer électroniquement.

    :param id: Identifiant unique du document.
    :type id: int
    :param doc_nom: Nom définitif du document.
    :type doc_nom: str
    :param doc_type: Type de document (contrat, convention, etc.).
    :type doc_type: str
    :param doc_sous_type: Sous-type de document.
    :type doc_sous_type: str
    :param priorite: Priorité du document (-1 : basse, 0 : normale, 1 : haute, 2 : urgente).
    :type priorite: int
    :param echeance: Délai en jours pour la signature (1-15 jours).
    :type echeance: int
    :param duree_archivage: Durée d'archivage du document en jours.
    :type duree_archivage: int
    :param description: Description du document.
    :type description: str
    :param chemin_fichier: Chemin du fichier stocké.
    :type chemin_fichier: str
    :param hash_fichier: Hash du fichier pour vérifier l'intégrité.
    :type hash_fichier: str
    :param id_user: Identifiant de l'utilisateur créateur du document.
    :type id_user: int
    :param cree_at: Date et heure de création du document.
    :type cree_at: datetime
    :param status: Statut du document (-2: annulé, -1: expiré, 0: en attente, 1: signé).
    :type status: int
    :param limite_signature: Date limite pour la signature (calculée).
    :type limite_signature: datetime
    :param complete_at: Date et heure de la complétion (signature finale).
    :type complete_at: datetime

    .. relations::
        - `user (User)`: Utilisateur créateur du document.
        - `points (List[Points])`: Liste des points de signature associés au document.
        - `invitation (List[Invitation])`: Liste des invitations associées au document.

    .. table:: `20_documents_a_signer`

    .. methods::
        `__repr__() -> str`: Représentation textuelle de l'objet DocToSigne.

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    __tablename__ = '20_documents_a_signer'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique du document"
    )
    doc_nom: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nom définitif du document"
    )
    doc_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type du document (contrat, convention, etc.)"
    )
    doc_sous_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Sous-type du document"
    )
    priorite: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Priorité du document (-1 : basse, 0 : normale, 1 : haute, 2 : urgente)"
    )
    echeance: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Échéance du document en jours (1-15)"
    )
    duree_archivage: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Durée d'archivage du document"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description du document"
    )

    # Métadonnées techniques
    chemin_fichier: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Chemin du fichier"
    )
    hash_fichier: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Hash du fichier pour intégrité"
    )
    id_user: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey(PK_USER),
        nullable=True,
        comment="Identifiant créateur"
    )
    cree_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(), # pylint: disable=E1102
        comment="Date de création du document"
    )

    # Statuts et dates
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Statut du document (-2: annulé, -1: expiré, 0: en attente, 1: signé)"
    )
    limite_signature: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        Computed("DATE_ADD(cree_at, INTERVAL echeance DAY)"),
        nullable=True,
        comment="Date limite de signature du document"
    )
    complete_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Date de complétion (signature finale) du document"
    )

    # Relations
    user = relationship(
        "User",
        back_populates="documents",
    )
    points = relationship(
        "Points",
        back_populates="document",
        cascade=CASCADE,
    )
    invitation = relationship(
        "Invitation",
        back_populates="document",
        cascade=CASCADE,
    )

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet DocToSigne.

        .. example :
            .. code-block:: python
            print(doc)
            >>> <DocToSigne(id=1, doc_nom='25092024_001_0001_Contr', status=0)>
        """
        return f"<DocToSigne(id={self.id}, doc_nom={self.doc_nom}, status={self.status})>"

    def download(self) -> Optional[io.BytesIO]:
        """Fonction pour télécharger le fichier du document à signer. Utilise la fonction
        `download_file` du module docs.py.

        :return: Fichier binaire téléchargé, ou None si échec.
        :rtype: Optional[io.BytesIO]

        .. example::
            .. code-block:: python
                file = doc.download()
                # or
                doc.download()
        """
        try:
            if self.chemin_fichier:
                with open(self.chemin_fichier, 'rb') as f:
                    file_data = f.read()
                    return io.BytesIO(file_data)
            return None
        except OSError:
            return None
