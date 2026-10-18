"""Blueprint pour la gestion des VPN.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from typing import Optional

from flask import (
    Blueprint,
    Response,
    render_template,
    redirect,
    url_for,
    session,
)
from werkzeug import Response as WResponse

from ..habilitations import validate_habilitation, VPN

vpn_bp = Blueprint(
    'vpn',
    __name__,
    url_prefix='/vpn'
)

@vpn_bp.get('/vpn')
@validate_habilitation(VPN)
def vpn(message: Optional[str] = None, success_message: Optional[str] = None,
        error_message: Optional[str] = None) -> str | Response:
    """
    Route pour l'accès à la page VPN.
    Gère l'affichage de la page VPN pour les utilisateurs habilités.
    Args:
        message (Optional[str]): Message à afficher.
        success_message (Optional[str]): Message de succès à afficher.
        error_message (Optional[str]): Message d'erreur à afficher.
    Returns:
        str | Response: Contenu HTML de la page VPN ou redirection en cas d'erreur.
    """
    habilitation = str(session.get('habilitation', ''))
    return render_template(
        'vpn.html',
        message=message,
        success_message=success_message,
        error_message=error_message,
        habilitation=habilitation
        )


@vpn_bp.get('/download/<access>')
@validate_habilitation(VPN)
def vpn_download(access: str) -> Response | WResponse:
    """
    Route pour le téléchargement d'une configuration VPN.
    Génère et retourne un fichier de configuration WireGuard selon le niveau d'accès.
    Args:
        access (str): Niveau d'accès demandé ('global', 'fichiers', 'charlemagne').
    Returns:
        Response: Fichier de configuration WireGuard ou redirection en cas d'erreur.
    """
    access = access.lower()
    # TODO : implémenter la génération des clés WireGuard éphémères
    # TODO : appeler l'API interne de la VM WireGuard pour enregistrer le peer
    # TODO : retourner le fichier .conf généré en téléchargement
    return redirect(url_for('vpn', error_message='Téléchargement VPN non encore disponible'))
