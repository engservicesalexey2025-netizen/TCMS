"""add expires at to user org access

Revision ID: 71823cab2087
Revises: 2da928a93b96
Create Date: 2026-07-29 15:40:00.000000

Временный доступ (доп. рекомендация №2 ТЗ) для оргединиц — тот же принцип
ExpiresAt, что и в UserRoles/UserPermissions/DataScopes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '71823cab2087'
down_revision: Union[str, None] = '2da928a93b96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('UserOrgAccess', sa.Column('ExpiresAt', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('UserOrgAccess', 'ExpiresAt')
