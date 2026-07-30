"""create security tables

Revision ID: 2da928a93b96
Revises: ee8c8951bf78
Create Date: 2026-07-29 15:35:00.000000

LoginHistory/PasswordHistory/UserSessions/PasswordResetTokens (§8/§9/§17
ТЗ) — не бизнес-сущности, без AuditMixin, по образцу AuditLog.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2da928a93b96'
down_revision: Union[str, None] = 'ee8c8951bf78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'LoginHistory',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('UserId', sa.UUID(), nullable=True),
        sa.Column('LoginAttempted', sa.String(length=100), nullable=False),
        sa.Column('Success', sa.Boolean(), nullable=False),
        sa.Column('Reason', sa.String(length=50), nullable=True),
        sa.Column('IpAddress', sa.String(length=45), nullable=True),
        sa.Column('UserAgent', sa.String(length=500), nullable=True),
        sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
    )

    op.create_table(
        'PasswordHistory',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('UserId', sa.UUID(), nullable=False),
        sa.Column('HashedPassword', sa.String(length=255), nullable=False),
        sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
    )

    op.create_table(
        'UserSessions',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('UserId', sa.UUID(), nullable=False),
        sa.Column('IssuedAt', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ExpiresAt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('RevokedAt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('IpAddress', sa.String(length=45), nullable=True),
        sa.Column('UserAgent', sa.String(length=500), nullable=True),
        sa.Column('ActingAsUserId', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ActingAsUserId'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
    )

    op.create_table(
        'PasswordResetTokens',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('UserId', sa.UUID(), nullable=False),
        sa.Column('TokenHash', sa.String(length=255), nullable=False),
        sa.Column('ExpiresAt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('UsedAt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
    )


def downgrade() -> None:
    op.drop_table('PasswordResetTokens')
    op.drop_table('UserSessions')
    op.drop_table('PasswordHistory')
    op.drop_table('LoginHistory')
