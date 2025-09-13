"""Renommage des champs camelCase en snake_case

Revision ID: b5f240cb2287
Revises: 
Create Date: 2025-09-13 17:14:15.828526

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b5f240cb2287'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Table 99_users
    op.alter_column('99_users', 'shaMdp', new_column_name='sha_mdp', existing_type=sa.String(255))
    op.alter_column('99_users', 'falseTest', new_column_name='false_test', existing_type=sa.Integer())

    # Table 01_contrats
    op.alter_column('01_contrats', 'Type', new_column_name='type_contrat', existing_type=sa.String(50))
    op.alter_column('01_contrats', 'SType', new_column_name='sous_type_contrat', existing_type=sa.String(50))
    op.alter_column('01_contrats', 'numContratExterne', new_column_name='id_externe_contrat', existing_type=sa.String(50))
    op.alter_column('01_contrats', 'dateDebut', new_column_name='date_debut', existing_type=sa.Date())
    op.alter_column('01_contrats', 'dateFinPreavis', new_column_name='date_fin_preavis', existing_type=sa.Date())
    op.alter_column('01_contrats', 'dateFin', new_column_name='date_fin', existing_type=sa.Date())

    # Table 11_documents
    op.alter_column('11_documents', 'idContrat', new_column_name='id_contrat', existing_type=sa.Integer())
    op.alter_column('11_documents', 'Type', new_column_name='type_document', existing_type=sa.String(50))
    op.alter_column('11_documents', 'SType', new_column_name='sous_type_document', existing_type=sa.String(50))
    op.alter_column('11_documents', 'strLien', new_column_name='str_lien', existing_type=sa.String(255))
    op.alter_column('11_documents', 'dateDocument', new_column_name='date_document', existing_type=sa.Date())

    # Table 12_evenements
    op.alter_column('12_evenements', 'idContrat', new_column_name='id_contrat', existing_type=sa.Integer())
    op.alter_column('12_evenements', 'dateEvenement', new_column_name='date_evenement', existing_type=sa.Date())
    op.alter_column('12_evenements', 'Type', new_column_name='type_evenement', existing_type=sa.String(50))
    op.alter_column('12_evenements', 'SType', new_column_name='sous_type_evenement', existing_type=sa.String(50))

    # Ajout des clés étrangères sur id_contrat
    op.create_foreign_key('fk_11_documents_id_contrat', '11_documents', '01_contrats', ['id_contrat'], ['id'])
    op.create_foreign_key('fk_12_evenements_id_contrat', '12_evenements', '01_contrats', ['id_contrat'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Table 99_users
    op.alter_column('99_users', 'sha_mdp', new_column_name='shaMdp', existing_type=sa.String(255))
    op.alter_column('99_users', 'false_test', new_column_name='falseTest', existing_type=sa.Integer())

    # Table 01_contrats
    op.alter_column('01_contrats', 'type_contrat', new_column_name='Type', existing_type=sa.String(50))
    op.alter_column('01_contrats', 'sous_type_contrat', new_column_name='SType', existing_type=sa.String(50))
    op.alter_column('01_contrats', 'id_externe_contrat', new_column_name='numContratExterne', existing_type=sa.String(50))
    op.alter_column('01_contrats', 'date_debut', new_column_name='dateDebut', existing_type=sa.Date())
    op.alter_column('01_contrats', 'date_fin_preavis', new_column_name='dateFinPreavis', existing_type=sa.Date())
    op.alter_column('01_contrats', 'date_fin', new_column_name='dateFin', existing_type=sa.Date())

    # Table 11_documents
    op.alter_column('11_documents', 'id_contrat', new_column_name='idContrat', existing_type=sa.Integer())
    op.alter_column('11_documents', 'type_document', new_column_name='Type', existing_type=sa.String(50))
    op.alter_column('11_documents', 'sous_type_document', new_column_name='SType', existing_type=sa.String(50))
    op.alter_column('11_documents', 'str_lien', new_column_name='strLien', existing_type=sa.String(255))
    op.alter_column('11_documents', 'date_document', new_column_name='dateDocument', existing_type=sa.Date())

    # Table 12_evenements
    op.alter_column('12_evenements', 'id_contrat', new_column_name='idContrat', existing_type=sa.Integer())
    op.alter_column('12_evenements', 'date_evenement', new_column_name='dateEvenement', existing_type=sa.Date())
    op.alter_column('12_evenements', 'type_evenement', new_column_name='Type', existing_type=sa.String(50))
    op.alter_column('12_evenements', 'sous_type_evenement', new_column_name='SType', existing_type=sa.String(50))

    # Suppression des clés étrangères sur id_contrat
    op.drop_constraint('fk_11_documents_id_contrat', '11_documents', type_='foreignkey')
    op.drop_constraint('fk_12_evenements_id_contrat', '12_evenements', type_='foreignkey')
