"""drop user role id column

Revision ID: a117eb778137
Revises: 924b8ee12d4b
Create Date: 2026-07-29 16:35:00.000000

Финальная уборка модуля доступа: Users.RoleId (единичная роль) больше не
используется — все данные уже перенесены в UserRoles (f6dffea2a98c), и ни
один роутер/сервис больше не читает user.Role.Code (require_roles удалён,
access.py переписан на get_active_role_ids/Roles.BypassDataScope).
Отдельная, более поздняя миграция, как и планировалось в
create_user_roles_migrate_data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a117eb778137'
down_revision: Union[str, None] = '924b8ee12d4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("Users_RoleId_fkey", "Users", type_="foreignkey")
    op.drop_column("Users", "RoleId")


def downgrade() -> None:
    op.add_column("Users", sa.Column("RoleId", sa.UUID(), nullable=True))
    bind = op.get_bind()
    # Восстанавливаем из UserRoles — берём первую активную роль пользователя
    # (после отката многие-ко-многим схлопывается обратно в одну роль).
    bind.execute(
        sa.text(
            'UPDATE "Users" u SET "RoleId" = ('
            '  SELECT ur."RoleId" FROM "UserRoles" ur '
            '  WHERE ur."UserId" = u."Id" AND ur."IsActive" = true '
            '  ORDER BY ur."CreatedDate" LIMIT 1'
            ')'
        )
    )
    op.alter_column("Users", "RoleId", nullable=False)
    op.create_foreign_key("Users_RoleId_fkey", "Users", "Roles", ["RoleId"], ["Id"])
