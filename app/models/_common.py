"""Module contenant les constantes et la base de données commune pour les modèles SQLAlchemy.

.. constants::
    - `PK_CONTRACT`: Clé primaire de la table des contrats.
    - `PK_DOC_TO_SIGNE`: Clé primaire de la table des documents à signer.
    - `PK_USER`: Clé primaire de la table des utilisateurs.
    - `PK_POINTS`: Clé primaire de la table des points.
    - `CASCADE`: Stratégie de suppression en cascade pour les relations.
    - `Base`: Classe de base pour les modèles SQLAlchemy.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
PK_CONTRACT = '01_contrats.id'
PK_DOC_TO_SIGNE = '20_documents_a_signer.id'
PK_USER = '99_users.id'
PK_POINTS = '23_points.id'
CASCADE = "all, delete-orphan"

__all__ = [
    "Base",
    "PK_CONTRACT",
    "PK_DOC_TO_SIGNE",
    "PK_USER",
    "PK_POINTS",
    "CASCADE",
]
