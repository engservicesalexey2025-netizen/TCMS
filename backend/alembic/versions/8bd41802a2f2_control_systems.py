"""control systems

Revision ID: 8bd41802a2f2
Revises: 576b0934fee3
Create Date: 2026-07-29 12:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8bd41802a2f2'
down_revision: Union[str, None] = '576b0934fee3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ControlSystems',
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

    op.add_column('Projects', sa.Column('ControlSystemId', sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_Projects_ControlSystemId", 'Projects', 'ControlSystems', ['ControlSystemId'], ['Id']
    )

    control_systems_table = sa.table(
        'ControlSystems',
        sa.column('Id', sa.UUID()),
        sa.column('Name', sa.String()),
        sa.column('IsActive', sa.Boolean()),
        sa.column('Version', sa.Integer()),
    )
    op.bulk_insert(control_systems_table, [
        {"Id": uuid.uuid4(), "Name": "Opera Build", "IsActive": True, "Version": 1},
        {"Id": uuid.uuid4(), "Name": "DES", "IsActive": True, "Version": 1},
    ])


def downgrade() -> None:
    op.drop_constraint("fk_Projects_ControlSystemId", 'Projects', type_='foreignkey')
    op.drop_column('Projects', 'ControlSystemId')
    op.drop_table('ControlSystems')
