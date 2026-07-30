"""add roles bypass and is system

Revision ID: d9a25fefcb05
Revises: 36ce585f765a
Create Date: 2026-07-29 15:50:00.000000

BypassDataScope заменяет хардкод UNRESTRICTED_ROLES = {ADMIN, DIVISION_DIRECTOR}
из app/services/access.py — сегодняшнее поведение переносится сюда данными,
а не кодом. IsSystem защищает 5 текущих ролей от удаления/переименования в
будущем «Конструкторе прав доступа».
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd9a25fefcb05'
down_revision: Union[str, None] = '36ce585f765a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BYPASS_ROLES = ("ADMIN", "DIVISION_DIRECTOR")


def upgrade() -> None:
    op.add_column('Roles', sa.Column('BypassDataScope', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('Roles', sa.Column('IsSystem', sa.Boolean(), server_default='false', nullable=False))

    bind = op.get_bind()
    bind.execute(sa.text('UPDATE "Roles" SET "IsSystem" = true'))
    for role_code in BYPASS_ROLES:
        bind.execute(
            sa.text('UPDATE "Roles" SET "BypassDataScope" = true WHERE "Code" = :code'),
            {"code": role_code},
        )


def downgrade() -> None:
    op.drop_column('Roles', 'IsSystem')
    op.drop_column('Roles', 'BypassDataScope')
