"""project gask fields

Revision ID: 576b0934fee3
Revises: ddb7eccfeb78
Create Date: 2026-07-29 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '576b0934fee3'
down_revision: Union[str, None] = 'ddb7eccfeb78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('Projects', sa.Column('GaskNotificationNumber', sa.String(length=100), nullable=True))
    op.drop_column('Projects', 'PlannedStartDate')
    op.drop_column('Projects', 'PlannedEndDate')


def downgrade() -> None:
    op.add_column('Projects', sa.Column('PlannedEndDate', sa.Date(), nullable=True))
    op.add_column('Projects', sa.Column('PlannedStartDate', sa.Date(), nullable=True))
    op.drop_column('Projects', 'GaskNotificationNumber')
