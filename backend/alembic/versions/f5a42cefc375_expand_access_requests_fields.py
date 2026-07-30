"""expand access requests fields

Revision ID: f5a42cefc375
Revises: 90050b2cfafe
Create Date: 2026-07-29 16:45:00.000000

Форма заявки на доступ по ТЗ (§4) — Телефон/Организация/Должность/Проект
в дополнение к уже существующим ФИО/Email/Роль/Подразделение.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f5a42cefc375'
down_revision: Union[str, None] = '90050b2cfafe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('AccessRequests', sa.Column('Phone', sa.String(length=50), nullable=True))
    op.add_column('AccessRequests', sa.Column('Organization', sa.String(length=255), nullable=True))
    op.add_column('AccessRequests', sa.Column('Position', sa.String(length=255), nullable=True))
    op.add_column('AccessRequests', sa.Column('RequestedProjectId', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_AccessRequests_RequestedProjectId', 'AccessRequests', 'Projects',
        ['RequestedProjectId'], ['Id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_AccessRequests_RequestedProjectId', 'AccessRequests', type_='foreignkey')
    op.drop_column('AccessRequests', 'RequestedProjectId')
    op.drop_column('AccessRequests', 'Position')
    op.drop_column('AccessRequests', 'Organization')
    op.drop_column('AccessRequests', 'Phone')
