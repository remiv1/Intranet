"""Conserve le point de migration des bases ayant deja applique b5f240cb2287.

La migration historique est archivee dans alembic/.arch. Ce marqueur permet
aux bases existantes de continuer vers les migrations actives sans rejouer
les renommages historiques.

Revision ID: b5f240cb2287
Revises:
"""

revision: str = 'b5f240cb2287'  # pylint: disable=C0103
down_revision: str | None = None  # pylint: disable=C0103
branch_labels: None = None  # pylint: disable=C0103
depends_on: None = None  # pylint: disable=C0103


def upgrade() -> None:
    """Point de compatibilite sans modification du schema."""


def downgrade() -> None:
    """Point de compatibilite sans modification du schema."""