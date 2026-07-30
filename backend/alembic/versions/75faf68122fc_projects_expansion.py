"""projects expansion

Revision ID: 75faf68122fc
Revises: aaa8dd36a540
Create Date: 2026-07-28 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '75faf68122fc'
down_revision: Union[str, None] = 'aaa8dd36a540'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _lookup_table(name: str) -> None:
    op.create_table(
        name,
        sa.Column('Name', sa.String(length=255), nullable=False),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('CreatedBy', sa.UUID(), nullable=True),
        sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ModifiedBy', sa.UUID(), nullable=True),
        sa.Column('IsActive', sa.Boolean(), nullable=False),
        sa.Column('Version', sa.Integer(), nullable=False),
        sa.Column('Comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
        sa.UniqueConstraint('Name'),
    )


def upgrade() -> None:
    # ### lookup tables backing the new creatable-select fields ###
    _lookup_table('ProjectTypes')
    _lookup_table('ProjectStages')
    _lookup_table('Contours')
    _lookup_table('ProjectSystems')

    op.create_table(
        'ProjectDocuments',
        sa.Column('ProjectId', sa.UUID(), nullable=False),
        sa.Column('FileName', sa.String(length=255), nullable=False),
        sa.Column('StoredPath', sa.String(length=500), nullable=False),
        sa.Column('FileSizeBytes', sa.Integer(), nullable=False),
        sa.Column('UploadedBy', sa.UUID(), nullable=True),
        sa.Column('UploadedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('CreatedBy', sa.UUID(), nullable=True),
        sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ModifiedBy', sa.UUID(), nullable=True),
        sa.Column('IsActive', sa.Boolean(), nullable=False),
        sa.Column('Version', sa.Integer(), nullable=False),
        sa.Column('Comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ProjectId'], ['Projects.Id'], ),
        sa.ForeignKeyConstraint(['UploadedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
    )
    op.create_index(op.f('ix_ProjectDocuments_ProjectId'), 'ProjectDocuments', ['ProjectId'], unique=False)

    # ### Основные данные ###
    op.add_column('Projects', sa.Column('CityId', sa.UUID(), nullable=True))
    op.add_column('Projects', sa.Column('Address', sa.String(length=500), nullable=True))
    op.add_column('Projects', sa.Column('Description', sa.Text(), nullable=True))

    # ### Проектные данные ###
    op.add_column('Projects', sa.Column('ProjectTypeId', sa.UUID(), nullable=True))
    op.add_column('Projects', sa.Column('ProjectStageId', sa.UUID(), nullable=True))
    op.add_column('Projects', sa.Column('ContourId', sa.UUID(), nullable=True))
    op.add_column('Projects', sa.Column('SystemId', sa.UUID(), nullable=True))

    # ### Подрядчики ###
    op.add_column('Projects', sa.Column('DeveloperId', sa.UUID(), nullable=True))
    op.add_column('Projects', sa.Column('ContractorId', sa.UUID(), nullable=True))
    op.add_column('Projects', sa.Column('GeneralContractorId', sa.UUID(), nullable=True))
    op.add_column('Projects', sa.Column('SubcontractorId', sa.UUID(), nullable=True))

    # ### Договор и характеристики ###
    op.add_column('Projects', sa.Column('ContractNumber', sa.String(length=100), nullable=True))
    op.add_column('Projects', sa.Column('GisLink', sa.String(length=500), nullable=True))

    # ### Даты и ГАСК — StartDate/EndDate renamed to Planned*, plus new fields.
    # Projects has zero rows today, so this is a straight add/drop, no data copy.
    op.add_column('Projects', sa.Column('GaskTicketNumber', sa.String(length=100), nullable=True))
    op.add_column('Projects', sa.Column('GaskTicketDate', sa.Date(), nullable=True))
    op.add_column('Projects', sa.Column('GaskTicketExpiryDate', sa.Date(), nullable=True))
    op.add_column('Projects', sa.Column('PlannedStartDate', sa.Date(), nullable=True))
    op.add_column('Projects', sa.Column('PlannedEndDate', sa.Date(), nullable=True))
    op.add_column('Projects', sa.Column('ActualEndDate', sa.Date(), nullable=True))
    op.drop_column('Projects', 'StartDate')
    op.drop_column('Projects', 'EndDate')

    op.create_foreign_key("fk_Projects_CityId", 'Projects', 'Cities', ['CityId'], ['Id'])
    op.create_foreign_key("fk_Projects_ProjectTypeId", 'Projects', 'ProjectTypes', ['ProjectTypeId'], ['Id'])
    op.create_foreign_key("fk_Projects_ProjectStageId", 'Projects', 'ProjectStages', ['ProjectStageId'], ['Id'])
    op.create_foreign_key("fk_Projects_ContourId", 'Projects', 'Contours', ['ContourId'], ['Id'])
    op.create_foreign_key("fk_Projects_SystemId", 'Projects', 'ProjectSystems', ['SystemId'], ['Id'])
    op.create_foreign_key("fk_Projects_DeveloperId", 'Projects', 'Contractors', ['DeveloperId'], ['Id'])
    op.create_foreign_key("fk_Projects_ContractorId", 'Projects', 'Contractors', ['ContractorId'], ['Id'])
    op.create_foreign_key(
        "fk_Projects_GeneralContractorId", 'Projects', 'Contractors', ['GeneralContractorId'], ['Id']
    )
    op.create_foreign_key(
        "fk_Projects_SubcontractorId", 'Projects', 'Contractors', ['SubcontractorId'], ['Id']
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### end Alembic commands ###
    op.drop_constraint("fk_Projects_SubcontractorId", 'Projects', type_='foreignkey')
    op.drop_constraint("fk_Projects_GeneralContractorId", 'Projects', type_='foreignkey')
    op.drop_constraint("fk_Projects_ContractorId", 'Projects', type_='foreignkey')
    op.drop_constraint("fk_Projects_DeveloperId", 'Projects', type_='foreignkey')
    op.drop_constraint("fk_Projects_SystemId", 'Projects', type_='foreignkey')
    op.drop_constraint("fk_Projects_ContourId", 'Projects', type_='foreignkey')
    op.drop_constraint("fk_Projects_ProjectStageId", 'Projects', type_='foreignkey')
    op.drop_constraint("fk_Projects_ProjectTypeId", 'Projects', type_='foreignkey')
    op.drop_constraint("fk_Projects_CityId", 'Projects', type_='foreignkey')

    op.add_column('Projects', sa.Column('EndDate', sa.Date(), nullable=True))
    op.add_column('Projects', sa.Column('StartDate', sa.Date(), nullable=True))
    op.drop_column('Projects', 'ActualEndDate')
    op.drop_column('Projects', 'PlannedEndDate')
    op.drop_column('Projects', 'PlannedStartDate')
    op.drop_column('Projects', 'GaskTicketExpiryDate')
    op.drop_column('Projects', 'GaskTicketDate')
    op.drop_column('Projects', 'GaskTicketNumber')
    op.drop_column('Projects', 'GisLink')
    op.drop_column('Projects', 'ContractNumber')
    op.drop_column('Projects', 'SubcontractorId')
    op.drop_column('Projects', 'GeneralContractorId')
    op.drop_column('Projects', 'ContractorId')
    op.drop_column('Projects', 'DeveloperId')
    op.drop_column('Projects', 'SystemId')
    op.drop_column('Projects', 'ContourId')
    op.drop_column('Projects', 'ProjectStageId')
    op.drop_column('Projects', 'ProjectTypeId')
    op.drop_column('Projects', 'Description')
    op.drop_column('Projects', 'Address')
    op.drop_column('Projects', 'CityId')

    op.drop_index(op.f('ix_ProjectDocuments_ProjectId'), table_name='ProjectDocuments')
    op.drop_table('ProjectDocuments')
    op.drop_table('ProjectSystems')
    op.drop_table('Contours')
    op.drop_table('ProjectStages')
    op.drop_table('ProjectTypes')
