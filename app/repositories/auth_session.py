"""Persistance, verification et revocation des sessions d'authentification."""

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models import AuthSession, User

INACTIVITY_TIMEOUT = timedelta(minutes=20)


class SessionStorageError(RuntimeError):
    """Signale qu'une session de navigateur ne peut pas etre enregistree."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_auth_session(
        database_session: Session,
        user_id: int,
        previous_token: str | None = None,
    ) -> str:
    """Prepare une nouvelle session dans la transaction courante.

    Args:
        database_session: Session SQLAlchemy responsable du commit.
        user_id: Compte authentifie.
        previous_token: Ancienne connexion du meme navigateur a remplacer.

    Returns:
        str: Jeton aleatoire destine au navigateur, jamais enregistre en clair.
    """
    if previous_token:
        revoke_auth_session(database_session, previous_token)
    token = token_urlsafe(32)
    now = _utcnow()
    database_session.add(AuthSession(
        token_hash=sha256(token.encode()).hexdigest(), id_user=user_id,
        created_at=now, last_seen_at=now, expires_at=now + INACTIVITY_TIMEOUT,
    ))
    return token


def revoke_auth_session(database_session: Session, token: str) -> None:
    """Revoque uniquement le navigateur identifie par le jeton.

    Args:
        database_session: Transaction responsable du commit.
        token: Jeton presente par le navigateur.
    """
    database_session.execute(delete(AuthSession).where(
        AuthSession.token_hash == sha256(token.encode()).hexdigest()
    ))


def revoke_user_sessions(database_session: Session, user_id: int) -> None:
    """Supprime les sessions du compte dans la transaction de modification.

    Args:
        database_session: Transaction de modification du compte.
        user_id: Compte dont toutes les sessions doivent etre revoquees.
    """
    database_session.execute(delete(AuthSession).where(AuthSession.id_user == user_id))


def validate_auth_session(database_session: Session, token: str | None) -> User | None:
    """Relit la session et le compte puis prolonge l'inactivite de vingt minutes.

    Args:
        database_session: Session de la requete, sans donnees utilisateur en cache.
        token: Jeton du navigateur, s'il existe.

    Returns:
        User | None: Compte courant autorise, ou None si une reconnexion est requise.
    """
    if not isinstance(token, str) or not token:
        return None
    token_hash = sha256(token.encode()).hexdigest()
    result = database_session.execute(
        select(AuthSession, User).join(User, User.id == AuthSession.id_user)
        .where(AuthSession.token_hash == token_hash)
    ).one_or_none()
    if result is None:
        return None
    stored_session, user = result
    now = _utcnow()
    if stored_session.expires_at <= now:
        revoke_auth_session(database_session, token)
        database_session.commit()
        return None
    if user.locked or (user.fin and user.fin <= date.today()) \
            or (user.debut and user.debut > date.today()):
        revoke_user_sessions(database_session, user.id)
        database_session.commit()
        return None
    refreshed = database_session.connection().execute(update(AuthSession).where(
        AuthSession.token_hash == token_hash, AuthSession.expires_at > now,
    ).values(last_seen_at=now, expires_at=now + INACTIVITY_TIMEOUT))
    database_session.commit()
    return user if refreshed.rowcount == 1 else None
