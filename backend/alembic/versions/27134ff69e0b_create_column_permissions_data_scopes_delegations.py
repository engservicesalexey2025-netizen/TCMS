"""create column permissions data scopes delegations

Revision ID: 27134ff69e0b
Revises: 624d94285cfc
Create Date: 2026-07-29 15:15:00.000000

ColumnPermissions (§14 ТЗ), DataScopes (§15 ТЗ), Delegations (доп.
рекомендация №3 ТЗ).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '27134ff69e0b'
down_revision: Union[str, None] = '624d94285cfc'
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
        'ColumnPermissions',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('EntityName', sa.String(length=100), nullable=False),
        sa.Column('FieldName', sa.String(length=100), nullable=False),
        sa.Column('RoleId', sa.UUID(), nullable=True),
        sa.Column('UserId', sa.UUID(), nullable=True),
        sa.Column('Mode', sa.String(length=10), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['RoleId'], ['Roles.Id'], ),
        sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
        sa.CheckConstraint(
            '("RoleId" IS NOT NULL) <> ("UserId" IS NOT NULL)',
            name='ck_column_permissions_role_xor_user',
        ),
    )

    op.create_table(
        'DataScopes',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('UserId', sa.UUID(), nullable=False),
        sa.Column('ScopeType', sa.String(length=20), nullable=False),
        sa.Column('ScopeId', sa.UUID(), nullable=False),
        sa.Column('ExpiresAt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('GrantedByUserId', sa.UUID(), nullable=True),
        sa.Column('Reason', sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['GrantedByUserId'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
        sa.UniqueConstraint('UserId', 'ScopeType', 'ScopeId'),
    )

    op.create_table(
        'Delegations',
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('FromUserId', sa.UUID(), nullable=False),
        sa.Column('ToUserId', sa.UUID(), nullable=False),
        sa.Column('RoleId', sa.UUID(), nullable=True),
        sa.Column('StartsAt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ExpiresAt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('Reason', sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['FromUserId'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ToUserId'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['RoleId'], ['Roles.Id'], ),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
    )


def downgrade() -> None:
    op.drop_table('Delegations')
    op.drop_table('DataScopes')
    op.drop_table('ColumnPermissions')
