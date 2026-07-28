"""audit action add delete

Revision ID: 459f830e2cf3
Revises: 101d5dd925ea
Create Date: 2026-07-28 15:33:29.660849

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '459f830e2cf3'
down_revision: Union[str, None] = '101d5dd925ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'DELETE'")


def downgrade() -> None:
    raise NotImplementedError(
        "Откат этой миграции не реализован: Postgres не умеет удалять "
        "значение enum (DELETE) без пересоздания типа audit_action."
    )
