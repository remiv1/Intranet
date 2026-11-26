"""Modèle représentant une invitation à signer un document.

.. classes::
    - `Invitation`: Représente une invitation à signer un document.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.sql import func

from ._common import Base, PK_DOC_TO_SIGNE, PK_USER

class Invitation(Base):
    """Représente une invitation à signer un document.

    :param id: Identifiant unique de l'invitation.
    :type id: int
    :param id_document: Identifiant du document à signer.
    :type id_document: int
    :param id_user: Identifiant de l'utilisateur invité.
    :type id_user: int
    :param token: Token sécurisé pour le lien d'invitation.
    :type token: str
    :param envoye_at: Date et heure d'envoi de l'invitation.
    :type envoye_at: datetime
    :param expire_at: Date et heure d'expiration de l'invitation.
    :type expire_at: datetime
    :param accede_at: Date et heure de la première consultation (nullable).
    :type accede_at: datetime
    :param signe_at: Date et heure de la signature (nullable).
    :type signe_at: datetime
    :param mail_envoye: Indique si l'e-mail a été envoyé.
    :type mail_envoye: bool
    :param mail_compte: Nombre de tentatives d'envoi d'e-mail.
    :type mail_compte: int
    :param code_otp: OTP pour validation finale (nullable).
    :type code_otp: str

    .. relations::
        - `document (DocToSigne)`: Document associé à l'invitation.
        - `user (User)`: Utilisateur invité.

    .. table:: `23_invitations`

    .. methods::
        - `__repr__() -> str`: Représentation textuelle de l'objet Invitation.

    .. author:: Rémi Verschuur <rverschuur@audit-io.fr>
    .. version:: 1.0.0
    """
    __tablename__ = '23_invitations'

    # Données principales
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique de l'invitation."
    )
    id_document: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_DOC_TO_SIGNE),
        nullable=False,
        comment="Identifiant du document associé à l'invitation."
    )
    id_user: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_USER),
        nullable=False,
        comment="Identifiant de l'utilisateur invité."
    )

    # Token sécurisé pour le lien
    token: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        comment="Token sécurisé pour le lien d'invitation."
    )

    # Statuts et dates
    envoye_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=func.now(), # pylint: disable=E1102
        comment="Date et heure d'envoi de l'invitation."
    )
    expire_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Date et heure d'expiration de l'invitation."
    )
    accede_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Date et heure de la première consultation (nullable)."
    )
    signe_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Date et heure de la signature (nullable)."
    )

    # Méta-données et OTP de validation
    mail_envoye: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Indique si l'e-mail a été envoyé."
    )
    mail_compte: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Nombre de tentatives d'envoi d'e-mail."
    )
    code_otp: Mapped[str] = mapped_column(
        String(6),
        nullable=True,
        comment="OTP pour validation finale (nullable)."
    )

    # Relations
    document = relationship(
        "DocToSigne",
        back_populates="invitation",
    )
    user = relationship("User")

    def __repr__(self) -> str:
        """Représentation de l'invitation.

        .. example::
            .. code-block:: python
            print(invitation)
            >>> <Invitation(id=1, document_id=5, user_id=3, envoye_at=2024-09-25 14:30:00,
            expire_at=2024-10-02 14:30:00)>
        """
        return f"<Invitation(id={self.id}, document_id={self.id_document}, " \
               f"user_id={self.id_user}, envoye_at={self.envoye_at}, " \
               f"expire_at={self.expire_at})>"
