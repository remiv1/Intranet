"""Initialisation des blueprints de l'application.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""

from .contracts import contracts_bp
from .signature import signatures_bp
from .vpn import vpn_bp

__all__ = [
    'contracts_bp',
    'signatures_bp',
    'vpn_bp',
]
