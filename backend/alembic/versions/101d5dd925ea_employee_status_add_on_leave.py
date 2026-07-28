"""employee status add on leave

Revision ID: 101d5dd925ea
Revises: d39510626fd4
Create Date: 2026-07-28 14:39:39.082542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '101d5dd925ea'
down_revision: Union[str, None] = 'd39510626fd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres нельзя добавить значение enum в той же транзакции, где оно
    # уже используется — отдельный autocommit-блок обязателен.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE employee_status ADD VALUE IF NOT EXISTS 'ON_LEAVE'")


def downgrade() -> None:
    # Postgres не поддерживает DROP VALUE для enum — миграция необратима
    # без пересоздания типа. Это осознанный компромисс, не баг.
    raise NotImplementedError(
        "Откат этой миграции не реализован: Postgres не умеет удалять "
        "значение enum (ON_LEAVE) без пересоздания типа employee_status."
    )
