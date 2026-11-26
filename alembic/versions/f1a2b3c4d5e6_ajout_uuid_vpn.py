"""Ajoute le lien vers le compte TTL-LAMa.

Revision ID: f1a2b3c4d5e6
Revises: d4f3a20e9b71
"""

import sqlalchemy as sa
from alembic import op

revision = 'f1a2b3c4d5e6'   # pylint: disable=C0103
down_revision = 'd4f3a20e9b71'   # pylint: disable=C0103
branch_labels = None   # pylint: disable=C0103
depends_on = None   # pylint: disable=C0103


def upgrade() -> None:
    """Ajoute la colonne vpn_uuid à la table 99_users.

    Cette colonne permet de stocker l'identifiant unique de l'utilisateur TTL-LAMa.
    """
    op.add_column( # pylint: disable=E1101
        '99_users',
        sa.Column('vpn_uuid', sa.String(36), nullable=True,
                  comment="Identifiant de l'utilisateur TTL-LAMa"),
    )
    op.add_column(   # pylint: disable=E1101
        '99_users',
        sa.Column('vpn_profiles', sa.JSON(), nullable=True)   # pylint: disable=E1101
    )
    op.add_column(   # pylint: disable=E1101
        '99_users',
        sa.Column('vpn_sync_state', sa.String(20), nullable=True)   # pylint: disable=E1101
    )
    op.add_column(   # pylint: disable=E1101
        '99_users',
        sa.Column(
            'vpn_password_dirty',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('0')
        ),
    )
    op.create_unique_constraint(   # pylint: disable=E1101
        'uq_99_users_vpn_uuid',
        '99_users',
        ['vpn_uuid'],
    )


def downgrade() -> None:
    """Retour à la version précédente"""
    op.drop_constraint('uq_99_users_vpn_uuid', '99_users', type_='unique') # pylint: disable=E1101
    op.drop_column('99_users', 'vpn_password_dirty') # pylint: disable=E1101
    op.drop_column('99_users', 'vpn_sync_state') # pylint: disable=E1101
    op.drop_column('99_users', 'vpn_profiles') # pylint: disable=E1101
    op.drop_column('99_users', 'vpn_uuid') # pylint: disable=E1101
