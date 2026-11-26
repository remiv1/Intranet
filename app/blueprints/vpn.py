"""Accès VPN utilisateur via TTL-LAMa.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""

import re
from typing import TypeGuard, cast

from flask import Blueprint, Response, abort, g, jsonify, render_template, request, session
from ttlama_sdk.errors import APIError
from werkzeug.exceptions import BadRequest

from ..habilitations import VPN, validate_habilitation
from ..ttlama import VPNSyncError, user_client

vpn_bp = Blueprint('vpn', __name__, url_prefix='/vpn')
INVALID_RESPONSE = 'Réponse TTL-LAMa invalide.'
INVALID_DURATION = 'Durée invalide'
JsonObject = dict[str, object]


@vpn_bp.after_request
def no_cache(response: Response) -> Response:
    """Ajoute des en-têtes pour empêcher la mise en cache des réponses."""
    response.headers['Cache-Control'] = 'no-store'
    return response


@vpn_bp.errorhandler(VPNSyncError)
def sync_error(error: VPNSyncError) -> tuple[Response, int]:
    """Gestion des erreurs de synchronisation VPN."""
    return jsonify(error=str(error)), 503


@vpn_bp.errorhandler(APIError)
def api_error(error: APIError) -> tuple[Response, int]:
    """Gestion des erreurs de l'API TTL-LAMa pour le VPN."""
    status = error.status_code
    if status in (400, 404, 409):
        return jsonify(error='Cette opération VPN est invalide ou indisponible.'), status
    response: dict[str, object] = {
        'error': 'Opération VPN non confirmée. Vérifiez son état avant de réessayer.'
    }
    if error.lease_id is not None:
        response['lease_id'] = error.lease_id
    return jsonify(response), 503


@vpn_bp.errorhandler(BadRequest)
def bad_request(_error: BadRequest) -> tuple[Response, int]:
    """Gestion des erreurs de requête incorrecte pour le VPN."""
    return jsonify(error='Données VPN invalides.'), 400


def _body(fields: set[str]) -> JsonObject:
    """Récupère et valide le corps JSON de la requête."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400)
    payload = cast(JsonObject, data)
    if set(payload) != fields:
        abort(400)
    return payload


def _positive_id(value: object) -> TypeGuard[int]:
    """Vérifie si la valeur est un identifiant positif."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _objects(value: object) -> list[JsonObject] | None:
    """Valide une liste d'objets JSON retournée par l'API."""
    if not isinstance(value, list):
        return None
    items = cast(list[object], value)
    if any(not isinstance(item, dict) for item in items):
        return None
    return cast(list[JsonObject], items)


def _object(value: object) -> JsonObject | None:
    """Valide un objet JSON retourné par l'API."""
    return cast(JsonObject, value) if isinstance(value, dict) else None


def _duration_seconds(value: object) -> int:
    """Convertit une durée au format 'XdXhXmXs' en secondes."""
    if not isinstance(value, str) or not value or len(value) > 100:
        raise ValueError(INVALID_DURATION)
    parts = re.findall(r'(\d{1,100})([dhms])', value)
    if ''.join(number + unit for number, unit in parts) != value:
        raise ValueError(INVALID_DURATION)
    seconds = sum(int(number) * {'d': 86400, 'h': 3600, 'm': 60, 's': 1}[unit]
                  for number, unit in parts)
    if seconds <= 0:
        raise ValueError(INVALID_DURATION)
    return seconds


@vpn_bp.get('/vpn')
@validate_habilitation(VPN)
def vpn() -> str:
    """Affiche la page VPN pour l'utilisateur courant."""
    return render_template('vpn.html', habilitation=str(session.get('habilitation', '')),
                           vpn_user_id=g.current_user.vpn_uuid or '')


@vpn_bp.get('/api/state')
@validate_habilitation(VPN)
def state() -> Response:
    """Récupère l'état actuel des appareils, profils et baux VPN de l'utilisateur."""
    with user_client(g.current_user) as client:
        overview = client.me.overview()
        devices = _objects(client.me.devices.list())
        leases = _objects(overview.get('leases'))
        profiles = _objects(overview.get('profiles'))
        if devices is None or leases is None or profiles is None:
            raise VPNSyncError(INVALID_RESPONSE)
        if any(not isinstance(lease.get('created_at'), str)
               or not _positive_id(lease.get('id')) for lease in leases):
            raise VPNSyncError(INVALID_RESPONSE)
        latest = sorted(leases, key=lambda lease: (lease['created_at'], lease['id']),
                        reverse=True)[:5]
        return jsonify(devices=devices, profiles=profiles, leases=latest)


@vpn_bp.post('/api/devices')
@validate_habilitation(VPN)
def create_device() -> tuple[Response, int]:
    """Crée un nouvel appareil VPN pour l'utilisateur courant."""
    data = _body({'name', 'public_key'})
    name = data['name']
    public_key = data['public_key']
    if (not isinstance(name, str) or not 1 <= len(name.strip()) <= 255
            or name != name.strip() or not isinstance(public_key, str)
            or not re.fullmatch(r'[A-Za-z0-9+/]{43}=', public_key)):
        abort(400)
    with user_client(g.current_user) as client:
        return jsonify(client.me.devices.create(name, public_key)), 201


@vpn_bp.post('/api/devices/<int:device_id>/delete')
@validate_habilitation(VPN)
def delete_device(device_id: int) -> Response:
    """Supprime un appareil VPN existant pour l'utilisateur courant."""
    with user_client(g.current_user) as client:
        client.me.devices.delete(device_id)
    return jsonify(success=True)


@vpn_bp.post('/api/leases')
@validate_habilitation(VPN)
def create_lease() -> tuple[Response, int]:
    """Crée un nouveau bail VPN pour l'utilisateur courant."""
    data = _body({'device_id', 'profile_id', 'duration_minutes'})
    device_id = data['device_id']
    profile_id = data['profile_id']
    minutes = data['duration_minutes']
    if (not _positive_id(device_id) or not _positive_id(profile_id)
            or not _positive_id(minutes)):
        abort(400)
    with user_client(g.current_user) as client:
        overview = client.me.overview()
        devices = _objects(overview.get('devices'))
        profiles = _objects(overview.get('profiles'))
        if devices is None or profiles is None:
            raise VPNSyncError(INVALID_RESPONSE)
        device = next((item for item in devices
                       if item.get('id') == device_id and item.get('revoked_at') is None), None)
        profile = next((item for item in profiles if item.get('id') == profile_id), None)
        policy = _object(profile.get('policy')) if profile else None
        if not device or policy is None:
            abort(400)
        try:
            maximum = _duration_seconds(policy.get('maximum_duration'))
        except ValueError as error:
            raise VPNSyncError('La politique du profil VPN est invalide.') from error
        if minutes * 60 > maximum:
            abort(400)
        return jsonify(client.me.leases.create(device_id, profile_id, duration=f'{minutes}m')), 201


@vpn_bp.get('/api/leases/<int:lease_id>/configuration')
@validate_habilitation(VPN)
def lease_configuration(lease_id: int) -> Response:
    """Récupère la configuration d'un bail VPN existant pour l'utilisateur courant."""
    with user_client(g.current_user) as client:
        return jsonify(client.me.leases.configuration(lease_id))


@vpn_bp.post('/api/leases/<int:lease_id>/revoke')
@validate_habilitation(VPN)
def revoke_lease(lease_id: int) -> Response:
    """Révoque un bail VPN existant pour l'utilisateur courant."""
    with user_client(g.current_user) as client:
        return jsonify(client.me.leases.revoke(lease_id))
