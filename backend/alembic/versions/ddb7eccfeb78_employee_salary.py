"""employee salary

Revision ID: ddb7eccfeb78
Revises: f3af66a01481
Create Date: 2026-07-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ddb7eccfeb78'
down_revision: Union[str, None] = 'f3af66a01481'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('Employees', sa.Column('Salary', sa.Numeric(14, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('Employees', 'Salary')
