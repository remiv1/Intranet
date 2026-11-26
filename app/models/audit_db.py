"""Audit database models.

..classes::
    - `AuditLog`: Représentation de l'historique des actions sur les documents à signer.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.sql import func

from ._common import Base, PK_DOC_TO_SIGNE, PK_USER

class AuditLog(Base):   # pylint: disable=R0903
    """
    Représentation de l'historique des actions sur les documents à signer.

    :param id: Identifiant unique de l'entrée de log.
    :type id: int
    :param id_document: Identifiant du document concerné.
    :type id_document: int
    :param id_user: Identifiant de l'utilisateur ayant effectué l'action (nullable).
    :type id_user: int
    :param action: Type d'action effectuée (-2: annulé, -1: expiré, 0: créé, 1: consulté,
    2: signé, 3: expédié).
    :type action: int
    :param details: Détails supplémentaires sur l'action (nullable).
    :type details: str
    :param ip_addresse: Adresse IP de l'utilisateur au moment de l'action (nullable).
    :type ip_addresse: str
    :param user_agent: User-Agent du navigateur au moment de l'action (nullable).
    :type user_agent: str
    :param timestamp: Date et heure de l'action.
    :type timestamp: datetime

    .. relations :
        document (DocToSigne): Document concerné par l'action.
        user (User): Utilisateur ayant effectué l'action (nullable).
    Méthodes :
        __repr__() -> str: Représentation textuelle de l'objet AuditLog.
    """
    __tablename__ = '24_audit_logs'

    # Données principales
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique de l'entrée de log"
    )
    id_document: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_DOC_TO_SIGNE),
        nullable=False,
        comment="Identifiant du document concerné"
    )
    id_user: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_USER),
        nullable=True,
        comment="Identifiant de l'utilisateur ayant effectué l'action (nullable)"
    )

    # Événement
    action: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Type d'action effectuée (-2=annulé, -1=exp., 0=créé, 1=cons., 2=signé, 3=exp.)"
    )
    details: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Détails supplémentaires sur l'action (nullable)"
    )

    # Contexte technique
    ip_addresse: Mapped[str] = mapped_column(
        String(45),
        nullable=True,
        comment="Adresse IP de l'utilisateur au moment de l'action (nullable)"
    )
    user_agent: Mapped[str] = mapped_column(
        String(1024),
        nullable=True,
        comment="User-Agent du navigateur au moment de l'action (nullable)"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(), # pylint: disable=E1102
        comment="Date et heure de l'action"
    )

    # Relations
    document = relationship("DocToSigne")
    user = relationship("User")

    def __repr__(self) -> str:
        """Représentation textuelle de l'objet AuditLog.

        .. exemple::
            .. code-block:: python
                print(audit_log)
                >>> <AuditLog(id=1, consultation le 2024-09-25 14:30:00)>
        """
        action = {
            -2: "annulation",
            -1: "expiré",
             0: "création",
             1: "consultation",
             2: "signature",
             3: "expédition"
        }.get(self.action, "inconnu")
        return f"<AuditLog(id={self.id}, {action} le {self.timestamp})>"
