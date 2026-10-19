"""Module contenant des constantes et des configurations communes pour la gestion des signatures.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""

from __future__ import annotations

from os import getenv

BAD_INVITATION = 'Invitation invalide ou non trouvée.'
DEFAULT_TEMP_DIR = getenv('DEFAULT_TEMP_DIR', '/tmp/')
