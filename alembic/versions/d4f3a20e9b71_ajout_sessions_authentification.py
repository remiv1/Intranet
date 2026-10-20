"""Ajout des sessions d'authentification revocables.

Revision ID: d4f3a20e9b71
Revises: 
"""

import sqlalchemy as sa
from alembic import op

revision: str = 'd4f3a20e9b71'  # pylint: disable=C0103
down_revision: str = None  # pylint: disable=C0103
branch_labels: None = None  # pylint: disable=C0103
depends_on: None = None  # pylint: disable=C0103


def upgrade() -> None:
    """Cree la table des sessions et ses index de recherche et d'expiration."""
    op.create_table(    # pylint: disable=E1101
        '98_sessions',
        sa.Column(
            'token_hash',
            sa.String(64), primary_key=True,
            comment="Empreinte du token de session."
        ),
        sa.Column(
            'id_user',
            sa.Integer(),
            nullable=False,
            comment="Identifiant de l'utilisateur associé à la session."
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            comment="Date et heure de création de la session."
        ),
        sa.Column(
            'last_seen_at',
            sa.DateTime(),
            nullable=False,
            comment="Date et heure de la dernière activité de la session."
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(),
            nullable=False,
            comment="Date et heure d'expiration de la session."
        ),
        sa.ForeignKeyConstraint(['id_user'], ['99_users.id'], ondelete='CASCADE'),
    )
    op.create_index(    # pylint: disable=E1101
        'ix_98_sessions_id_user',
        '98_sessions',
        ['id_user'],
    )
    op.create_index(    # pylint: disable=E1101
        'ix_98_sessions_expires_at',
        '98_sessions',
        ['expires_at'],
    )


def downgrade() -> None:
    """Supprime la table des sessions, invalidant les connexions existantes."""
    op.drop_table('98_sessions')    # pylint: disable=E1101
