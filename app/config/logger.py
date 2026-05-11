"""Module de configuration du logger de l'application."""

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
