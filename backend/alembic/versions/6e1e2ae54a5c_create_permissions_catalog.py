"""create permissions catalog

Revision ID: 6e1e2ae54a5c
Revises: a4d21adffcbb
Create Date: 2026-07-29 15:05:00.000000

Permissions/RolePermissions/UserPermissions/UserRoles — ядро RBAC (МОДУЛЬ 001,
§10/§18). UserRoles заменяет прежний единичный Users.RoleId (многие-ко-многим);
сама колонка Users.RoleId удаляется отдельной, более поздней миграцией — после
того как код перестанет её читать.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6e1e2ae54a5c'
down_revision: Union[str, None] = 'a4d21adffcbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list:
    return [
        sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('CreatedBy', sa.UUID(), nullable=True),
        sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ModifiedBy', sa.UUID(), nullable=True),
        sa.Column('IsActive', sa.Boolean(), nullable=False),
        sa.Column('Version', sa.Integer(), nullable=False),
        sa.Column('Comment', sa.Text(), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        'Permissions',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('Module', sa.String(length=50), nullable=False),
        sa.Column('Action', sa.String(length=20), nullable=False),
        sa.Column('Code', sa.String(length=80), nullable=False),
        sa.Column('Name', sa.String(length=255), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
        sa.UniqueConstraint('Module', 'Action'),
        sa.UniqueConstraint('Code'),
    )

    op.create_table(
        'RolePermissions',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('RoleId', sa.UUID(), nullable=False),
        sa.Column('PermissionId', sa.UUID(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['RoleId'], ['Roles.Id'], ),
        sa.ForeignKeyConstraint(['PermissionId'], ['Permissions.Id'], ),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
        sa.UniqueConstraint('RoleId', 'PermissionId'),
    )

    op.create_table(
        'UserPermissions',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('UserId', sa.UUID(), nullable=False),
        sa.Column('PermissionId', sa.UUID(), nullable=False),
        sa.Column('Effect', sa.String(length=6), nullable=False),
        sa.Column('ExpiresAt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('Reason', sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['PermissionId'], ['Permissions.Id'], ),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
        sa.UniqueConstraint('UserId', 'PermissionId'),
    )

    op.create_table(
        'UserRoles',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('UserId', sa.UUID(), nullable=False),
        sa.Column('RoleId', sa.UUID(), nullable=False),
        sa.Column('ExpiresAt', sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['RoleId'], ['Roles.Id'], ),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
        sa.UniqueConstraint('UserId', 'RoleId'),
    )


def downgrade() -> None:
    op.drop_table('UserRoles')
    op.drop_table('UserPermissions')
    op.drop_table('RolePermissions')
    op.drop_table('Permissions')
