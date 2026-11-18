"""Module de configuration de l'API TTL-LAMa.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
from __future__ import annotations

from os import getenv
from dataclasses import dataclass

@dataclass
class ConfigTTLLama:
    """Paramètres du compte administrateur de l'API TTL-LAMa."""

    URL: str = getenv('TTL_LAMA_URL', '') # pylint: disable=C0103
    ADMIN_USERNAME: str = getenv('TTL_LAMA_ADMIN_USERNAME', '') # pylint: disable=C0103
    ADMIN_PASSWORD: str = getenv('TTL_LAMA_ADMIN_PASSWORD', '') # pylint: disable=C0103
    ALLOW_HTTP: bool = getenv('TTL_LAMA_ALLOW_HTTP', '').lower() in ('1', 'true', 'yes') # pylint: disable=C0103
