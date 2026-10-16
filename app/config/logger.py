"""Module de configuration du logger de l'application.

.. constants::
    - `api_logger`: L'objet logger utilisé pour l'application.

.. author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""

import logging

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler("application.log"),
        logging.StreamHandler()
    ]
)
api_logger = logging.getLogger(__name__)
