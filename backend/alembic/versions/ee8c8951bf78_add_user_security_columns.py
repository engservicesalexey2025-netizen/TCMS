"""add user security columns

Revision ID: ee8c8951bf78
Revises: f6dffea2a98c
Create Date: 2026-07-29 15:30:00.000000

Поля для блокировки после неудачных попыток входа, принудительной смены
пароля и 2FA (§6/§8/доп. рекомендация №1 ТЗ). Безопасно на таблице с одной
существующей строкой — все новые колонки nullable либо со значением по
умолчанию.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ee8c8951bf78'
down_revision: Union[str, None] = 'f6dffea2a98c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('Users', sa.Column('FailedLoginAttempts', sa.Integer(), server_default='0', nullable=False))
    op.add_column('Users', sa.Column('LockedUntil', sa.DateTime(timezone=True), nullable=True))
    op.add_column('Users', sa.Column('LastLoginAt', sa.DateTime(timezone=True), nullable=True))
    op.add_column('Users', sa.Column('LastLoginIp', sa.String(length=45), nullable=True))
    op.add_column('Users', sa.Column('PasswordChangedAt', sa.DateTime(timezone=True), nullable=True))
    op.add_column('Users', sa.Column('MustChangePassword', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('Users', sa.Column('MfaEnabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('Users', sa.Column('MfaSecret', sa.String(length=255), nullable=True))
    op.add_column('Users', sa.Column('MfaRecoveryCodesHash', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('Users', 'MfaRecoveryCodesHash')
    op.drop_column('Users', 'MfaSecret')
    op.drop_column('Users', 'MfaEnabled')
    op.drop_column('Users', 'MustChangePassword')
    op.drop_column('Users', 'PasswordChangedAt')
    op.drop_column('Users', 'LastLoginIp')
    op.drop_column('Users', 'LastLoginAt')
    op.drop_column('Users', 'LockedUntil')
    op.drop_column('Users', 'FailedLoginAttempts')
