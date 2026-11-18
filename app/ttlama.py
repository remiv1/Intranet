"""Synchronisation des droits VPN avec l'API TTL-LAMa."""

from collections.abc import Generator
from contextlib import contextmanager
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy.orm import Session
from ttlama_sdk import TTLLama
from ttlama_sdk.errors import APIError

from .config.config import ConfigTTLLama
from .models import User


class VPNSyncError(Exception):
    """Une opération VPN n'a pas pu être confirmée."""


@contextmanager
def admin_client() -> Generator[TTLLama, None, None]:
    """Ouvre une session administrateur temporaire, sans journaliser ses secrets."""
    url = ConfigTTLLama.URL
    parts = urlsplit(url)
    if not url or not ConfigTTLLama.ADMIN_USERNAME or not ConfigTTLLama.ADMIN_PASSWORD:
        raise VPNSyncError('Configuration TTL-LAMa incomplète.')
    if parts.scheme != 'https' and not (parts.scheme == 'http' and ConfigTTLLama.ALLOW_HTTP):
        raise VPNSyncError('La connexion TTL-LAMa doit utiliser HTTPS.')
    try:
        client = TTLLama(url, timeout=5.0)
    except ValueError as error:
        raise VPNSyncError('Adresse TTL-LAMa invalide.') from error
    try:
        client.login(ConfigTTLLama.ADMIN_USERNAME, ConfigTTLLama.ADMIN_PASSWORD)
        yield client
    except APIError as error:
        raise VPNSyncError('Service TTL-LAMa indisponible ou opération non confirmée.') from error
    finally:
        if client.token:
            try:
                client.auth.logout()
            except APIError:
                pass
        client.close()


def active_profiles(client: TTLLama) -> list[dict[str, object]]:
    """Retourne les profils actifs après validation des données de l'API."""
    profiles: list[dict[str, object]] = []
    for profile in client.profile.list():
        profile_id = profile.get('id')
        name = profile.get('name')
        if not isinstance(profile_id, int) or profile_id <= 0 or not isinstance(name, str):
            raise VPNSyncError('Réponse TTL-LAMa invalide.')
        if profile.get('revoked_at') is None:
            profiles.append({'id': profile_id, 'name': name})
    return profiles


def assigned_profiles(client: TTLLama, user_uuid: str) -> set[int]:
    """Retourne les identifiants des attributions actives."""
    assigned: set[int] = set()
    for assignment in client.user.profiles(user_uuid):
        profile_id = assignment.get('profile_id')
        if not isinstance(profile_id, int) or profile_id <= 0:
            raise VPNSyncError('Réponse TTL-LAMa invalide.')
        if assignment.get('revoked_at') is None:
            assigned.add(profile_id)
    return assigned


def profiles_for_habilitation(habilitation: int | None) -> set[int]:
    """Calcule les profils TTL-LAMa associés aux droits Intranet."""
    rights = set(str(habilitation or ''))
    profiles: set[int] = {2} if rights.intersection('12345') else set()
    if '1' in rights:
        profiles.add(1)
    if '3' in rights:
        profiles.add(3)
    return profiles


def available_profiles_for_habilitation(
    client: TTLLama,
    habilitation: int | None,
) -> list[dict[str, object]]:
    """Retourne les profils actifs du SDK qui correspondent aux droits Intranet."""
    required = profiles_for_habilitation(habilitation)
    profiles = [
        profile for profile in active_profiles(client)
        if profile.get('id') in required
    ]
    if {profile.get('id') for profile in profiles} != required:
        raise VPNSyncError('Un profil TTL-LAMa requis est indisponible.')
    return profiles


def _lock_user(database: Session, user_id: int) -> User:
    user = database.query(User).filter(User.id == user_id).with_for_update().one_or_none()
    if user is None:
        raise VPNSyncError('Utilisateur introuvable.')
    return user


def _active_profile_ids(client: TTLLama) -> set[int]:
    return {
        profile_id
        for profile in active_profiles(client)
        if isinstance(profile_id := profile.get('id'), int)
    }


def _selected_profile_ids(client: TTLLama, user: User) -> set[int]:
    profiles = profiles_for_habilitation(user.habilitation)
    if not profiles or not profiles.issubset(_active_profile_ids(client)):
        raise VPNSyncError('La sélection des profils VPN est invalide.')
    return profiles


def _create_user(
    database: Session,
    user: User,
    client: TTLLama,
) -> User:
    _selected_profile_ids(client, user)
    password_at_creation = user.sha_mdp
    user_id = user.id
    user.vpn_sync_state = 'creating'
    database.commit()
    try:
        result = client.user.create(
            user.identifiant or '',
            email=user.mail or None,
            password=password_at_creation,
        )
        user_uuid = str(UUID(result['id']))
    except (APIError, KeyError, TypeError, ValueError) as error:
        user = _lock_user(database, user_id)
        user.vpn_sync_state = 'review'
        database.commit()
        raise VPNSyncError(
            'Création VPN non confirmée : vérification manuelle nécessaire.'
        ) from error

    user = _lock_user(database, user_id)
    user.vpn_uuid = user_uuid
    user.vpn_sync_state = 'pending'
    user.vpn_password_dirty = user.sha_mdp != password_at_creation
    database.commit()
    return _lock_user(database, user_id)


def _user_changes(user: User, remote: dict[str, object]) -> dict[str, object]:
    changes: dict[str, object] = {}
    username = user.identifiant or ''
    email = user.mail or None
    if remote.get('username') != username:
        changes['username'] = username
    if remote.get('email') != email:
        changes['email'] = email
    if remote.get('enabled') is not True:
        changes['enabled'] = True
    if user.vpn_password_dirty:
        changes['password'] = user.sha_mdp
    return changes


def _sync_profiles(client: TTLLama, user: User, profiles: set[int]) -> None:
    if user.vpn_uuid is None:
        return
    current = assigned_profiles(client, user.vpn_uuid)
    for profile_id in sorted(current - profiles):
        client.user.unassign_profile(user.vpn_uuid, profile_id)
    for profile_id in sorted(profiles - current):
        client.user.assign_profile(user.vpn_uuid, profile_id)


def _sync_enabled_user(client: TTLLama, user: User) -> None:
    profiles = _selected_profile_ids(client, user)
    if user.vpn_uuid is None:
        raise VPNSyncError('Identifiant TTL-LAMa manquant.')
    changes = _user_changes(user, client.user.get(user.vpn_uuid))
    if changes:
        client.user.update(user.vpn_uuid, **changes)
    _sync_profiles(client, user, profiles)
    user.vpn_password_dirty = False


def _pending_user(database: Session, user_id: int) -> User | None:
    user = _lock_user(database, user_id)
    if user.vpn_sync_state in ('creating', 'review'):
        database.rollback()
        raise VPNSyncError('Création VPN à vérifier manuellement avant toute nouvelle tentative.')
    if user.vpn_sync_state != 'pending':
        database.rollback()
        return None
    return user


def sync_user(database: Session, user_id: int) -> None:
    """Applique l'état local durable ; une création incertaine exige une vérification humaine."""
    user = _pending_user(database, user_id)
    if user is None:
        return

    try:
        with admin_client() as client:
            enabled = '7' in str(user.habilitation or '')
            if enabled and not user.vpn_uuid:
                user = _create_user(database, user, client)
                enabled = '7' in str(user.habilitation or '')
            if user.vpn_uuid and enabled:
                _sync_enabled_user(client, user)
            elif user.vpn_uuid:
                client.user.delete(user.vpn_uuid)
            user.vpn_sync_state = 'synced'
            database.commit()
    except Exception:
        database.rollback()
        raise
