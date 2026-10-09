"""org units code manager and tree levels

Revision ID: 7be364163d7f
Revises: f5a42cefc375
Create Date: 2026-07-31 07:57:19.464757

Расширение оргструктуры до 5 уровней (Компания → Дивизион/Филиал →
Управление → Отдел → Группа) под модуль «Организационная структура»:
2 новых значения enum org_unit_type (ADD VALUE требует autocommit-блока —
тот же приём, что в 36ce585f765a) + Code/ManagerEmployeeId на OrgUnits.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7be364163d7f'
down_revision: Union[str, None] = 'f5a42cefc375'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('OrgUnits', sa.Column('Code', sa.String(length=50), nullable=True))
    op.add_column('OrgUnits', sa.Column('ManagerEmployeeId', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'OrgUnits', 'Employees', ['ManagerEmployeeId'], ['Id'])
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE org_unit_type ADD VALUE IF NOT EXISTS 'COMPANY'")
        op.execute("ALTER TYPE org_unit_type ADD VALUE IF NOT EXISTS 'SECTION'")


def downgrade() -> None:
    op.drop_constraint(None, 'OrgUnits', type_='foreignkey')
    op.drop_column('OrgUnits', 'ManagerEmployeeId')
    op.drop_column('OrgUnits', 'Code')
    raise NotImplementedError(
        "Откат значений enum COMPANY/SECTION не реализован: Postgres не умеет "
        "удалять значение enum без пересоздания типа org_unit_type."
    )
