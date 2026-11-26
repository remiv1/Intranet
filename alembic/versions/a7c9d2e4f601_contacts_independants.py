"""Contacts indépendants et associations multiples aux contrats."""
# pylint: disable=E1101

import sqlalchemy as sa
from sqlalchemy.sql.functions import count
from alembic import op

revision = 'a7c9d2e4f601' # pylint: disable=C0103
down_revision = 'f1a2b3c4d5e6' # pylint: disable=C0103
branch_labels = None # pylint: disable=C0103
depends_on = None # pylint: disable=C0103

FK_NAMES = {'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s'}
CONTACTS = sa.table('02_contacts', sa.column('id'), sa.column('id_contrat'))
ASSOCIATIONS = sa.table('02_contacts_contrats', sa.column('id_contact'), sa.column('id_contrat'))


def upgrade() -> None:
    """Conserve tous les rattachements existants dans la table d'association."""
    connection = op.get_bind() # pylint: disable=E1101
    foreign_keys = sa.inspect(connection).get_foreign_keys('02_contacts')
    op.create_table( # pylint: disable=E1101
        '02_contacts_contrats',
        sa.Column('id_contact', sa.Integer(), nullable=False),
        sa.Column('id_contrat', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_contact'], ['02_contacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_contrat'], ['01_contrats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_contact', 'id_contrat'),
    )
    op.create_index( # pylint: disable=E1101
        'ix_02_contacts_contrats_id_contrat',
        '02_contacts_contrats',
        ['id_contrat'],
    )
    connection.execute(ASSOCIATIONS.insert().from_select(
        ['id_contact', 'id_contrat'], sa.select(CONTACTS.c.id, CONTACTS.c.id_contrat)
    ))
    with op.batch_alter_table(
        '02_contacts',
        naming_convention=FK_NAMES,
    ) as batch:
        for foreign_key in foreign_keys:
            if foreign_key['constrained_columns'] == ['id_contrat']:
                batch.drop_constraint(
                    foreign_key['name'] or 'fk_02_contacts_id_contrat_01_contrats',
                    type_='foreignkey',
                )
        batch.drop_column('id_contrat')


def downgrade() -> None:
    """Refuse un retour arrière qui ferait perdre des contacts ou des liens."""
    connection = op.get_bind()
    incompatible = connection.execute(
        sa.select(CONTACTS.c.id).select_from(CONTACTS.outerjoin(
            ASSOCIATIONS, ASSOCIATIONS.c.id_contact == CONTACTS.c.id
        )).group_by(CONTACTS.c.id).having(count(ASSOCIATIONS.c.id_contrat) != 1).limit(1)
    ).first()
    if incompatible is not None:
        raise RuntimeError(
            'Retour arrière impossible : chaque contact doit avoir exactement un contrat.'
        )
    op.add_column(
        '02_contacts',
        sa.Column('id_contrat', sa.Integer(), nullable=True),
    )
    connection.execute(CONTACTS.update().values(id_contrat=sa.select(
        ASSOCIATIONS.c.id_contrat
    ).where(ASSOCIATIONS.c.id_contact == CONTACTS.c.id).scalar_subquery()))
    with op.batch_alter_table('02_contacts') as batch:
        batch.alter_column('id_contrat', existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key('fk_02_contacts_id_contrat_01_contrats',
                                 '01_contrats', ['id_contrat'], ['id'])
    op.drop_index('ix_02_contacts_contrats_id_contrat', table_name='02_contacts_contrats')
    op.drop_table('02_contacts_contrats')
