"""roles code to varchar

Revision ID: a4d21adffcbb
Revises: 1128acc25e2a
Create Date: 2026-07-29 15:00:00.000000

Модуль «Управление доступом и безопасностью» (МОДУЛЬ 001): администратор
должен уметь создавать новые роли (Лаборатория/Подрядчик/Заказчик и т.д.)
через интерфейс без миграции схемы — Postgres ENUM для Roles.Code этого не
позволяет (ALTER TYPE ADD VALUE — это деплой кода).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a4d21adffcbb'
down_revision: Union[str, None] = '1128acc25e2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'Roles',
        'Code',
        type_=sa.String(length=50),
        postgresql_using='"Code"::text',
        existing_nullable=False,
    )
    op.execute('DROP TYPE role_code')


def downgrade() -> None:
    role_code = sa.Enum(
        'ADMIN', 'DIVISION_DIRECTOR', 'DEPARTMENT_HEAD', 'GROUP_HEAD', 'OBSERVER',
        name='role_code',
    )
    role_code.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        'Roles',
        'Code',
        type_=role_code,
        postgresql_using='"Code"::role_code',
        existing_nullable=False,
    )
