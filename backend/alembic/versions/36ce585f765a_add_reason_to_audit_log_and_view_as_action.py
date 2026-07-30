"""add reason to audit log and view as action

Revision ID: 36ce585f765a
Revises: 71823cab2087
Create Date: 2026-07-29 15:45:00.000000

AuditLog.Reason — обоснование чувствительных изменений (напр. "выдан полный
доступ — временная замена HR на период отпуска", §12 ТЗ). AuditAction.VIEW_AS —
новое действие для журналирования "Просмотреть как пользователь" (доп.
рекомендация №4 ТЗ). ADD VALUE на существующий enum требует autocommit-блока
(тот же приём, что и в 459f830e2cf3_audit_action_add_delete.py).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '36ce585f765a'
down_revision: Union[str, None] = '71823cab2087'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('AuditLog', sa.Column('Reason', sa.Text(), nullable=True))
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'VIEW_AS'")


def downgrade() -> None:
    op.drop_column('AuditLog', 'Reason')
    raise NotImplementedError(
        "Откат значения enum VIEW_AS не реализован: Postgres не умеет "
        "удалять значение enum без пересоздания типа audit_action."
    )
