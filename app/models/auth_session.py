"""Sessions d'authentification revocables, stockees sous forme d'empreinte."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ._common import Base, PK_USER


class AuthSession(Base):
    """Represente la connexion d'un navigateur a un compte utilisateur."""

    __tablename__ = '98_sessions'

    token_hash: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="Empreinte du token de session."
    )
    id_user: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(PK_USER, ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Identifiant de l'utilisateur associé à la session."
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Date et heure de création de la session."
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Date et heure de la dernière activité de la session."
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        comment="Date et heure d'expiration de la session."
    )
