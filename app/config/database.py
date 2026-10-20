"""Module de configuration de la base de données pour l'application Flask.
Ce module définit la configuration de la base de données en utilisant les variables d'environnement
chargées depuis le fichier .env. Il utilise SQLAlchemy pour gérer la connexion à la base de données
et la création des tables. La fonction `initialize_database` est utilisée pour créer les tables
de la base de données avec un mécanisme de retry en cas d'erreur de connexion,
servant également de healthcheck pour l'application.

.. constants::
    - `engine`: L'objet SQLAlchemy Engine utilisé pour la connexion à la base de données.
    - `SESSION`: La session SQLAlchemy pour interagir avec la base de données.

.. author:: Rémi Verschuur <rverschuur@audit-io.fr>
.. version:: 1.0.0
"""
import time
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.config.config import ConfigDB
from ..models._common import Base

# Créer l'engin SQLAlchemy
engine = create_engine(
    ConfigDB.DB_URL,
    pool_recycle=1800,
    pool_timeout=30,
    pool_pre_ping=True,
    connect_args={'connect_timeout': 10},
    echo=False
)

# Créer les tables de la base de données (avec retry en cas d'erreur de connexion)
def initialize_database(max_retries: int = 10, retry_delay: int = 2) -> bool | None:
    """
    Fonction pour initialiser la base de données avec retry en cas d'erreur de connexion.
    Sert aussi de healthcheck pour l'application.
    :param max_retries: Le nombre maximum de tentatives de connexion.
    :type max_retries: int
    :param retry_delay: Le délai entre chaque tentative de connexion (en secondes).
    :type retry_delay: int
    :return: True si la connexion est réussie, None sinon.
    :rtype: bool | None
    """
    # Tenter de créer les tables avec des retries
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(engine, tables=[
                table for table in Base.metadata.sorted_tables if table.name != '98_sessions'
            ])
            if not inspect(engine).has_table('98_sessions'):
                raise RuntimeError(
                    "Appliquer la migration Alembic des sessions avant le démarrage."
                )
            return True
        except SQLAlchemyError as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise ImportError(
                f"Connection impossible à la BdD après {max_retries} tentatives : {e}"
            ) from e

# Créer une session de base de données sans ouverture de celle-ci
SESSION = sessionmaker(bind=engine)
