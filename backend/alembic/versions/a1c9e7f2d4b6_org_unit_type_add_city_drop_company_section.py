"""org unit type: add city, drop company/section

Revision ID: a1c9e7f2d4b6
Revises: 7be364163d7f
Create Date: 2026-07-31 09:00:00.000000

Клиент уточнил реальную структуру: Дивизион → Город (филиал, во главе
Директор филиала) → Управление (Руководитель управления) → Группа
(Руководитель группы) → Сотрудники. COMPANY и SECTION, добавленные
предыдущей миграцией, в этой структуре не нужны — а Postgres не даёт
удалить значение enum через ALTER TYPE, поэтому тип пересоздаётся целиком.
Безопасно только потому, что ни одна строка OrgUnits ещё не использует
COMPANY/SECTION (проверено перед написанием миграции).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1c9e7f2d4b6'
down_revision: Union[str, None] = '7be364163d7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE org_unit_type RENAME TO org_unit_type_old")
    op.execute("CREATE TYPE org_unit_type AS ENUM ('DIVISION', 'CITY', 'DEPARTMENT', 'GROUP')")
    op.execute(
        'ALTER TABLE "OrgUnits" ALTER COLUMN "UnitType" '
        'TYPE org_unit_type USING "UnitType"::text::org_unit_type'
    )
    op.execute("DROP TYPE org_unit_type_old")


def downgrade() -> None:
    op.execute("ALTER TYPE org_unit_type RENAME TO org_unit_type_new")
    op.execute(
        "CREATE TYPE org_unit_type AS ENUM ('COMPANY', 'DIVISION', 'DEPARTMENT', 'SECTION', 'GROUP')"
    )
    op.execute(
        'ALTER TABLE "OrgUnits" ALTER COLUMN "UnitType" '
        'TYPE org_unit_type USING "UnitType"::text::org_unit_type'
    )
    op.execute("DROP TYPE org_unit_type_new")
