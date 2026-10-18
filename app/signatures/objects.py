"""Module pour la gestion des objets liés aux signatures.

.. module_author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Signatory:
    id: int
    name: str
    email: Optional[str]

