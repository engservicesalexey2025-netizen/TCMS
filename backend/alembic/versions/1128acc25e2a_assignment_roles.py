"""assignment roles

Revision ID: 1128acc25e2a
Revises: 1991232d7554
Create Date: 2026-07-29 14:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1128acc25e2a'
down_revision: Union[str, None] = '1991232d7554'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'AssignmentRoles',
        sa.Column('Name', sa.String(length=255), nullable=False),
        sa.Column('Id', sa.UUID(), nullable=False),
        sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('CreatedBy', sa.UUID(), nullable=True),
        sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ModifiedBy', sa.UUID(), nullable=True),
        sa.Column('IsActive', sa.Boolean(), nullable=False),
        sa.Column('Version', sa.Integer(), nullable=False),
        sa.Column('Comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['CreatedBy'], ['Users.Id'], ),
        sa.ForeignKeyConstraint(['ModifiedBy'], ['Users.Id'], ),
        sa.PrimaryKeyConstraint('Id'),
        sa.UniqueConstraint('Name'),
    )

    roles_table = sa.table(
        'AssignmentRoles',
        sa.column('Id', sa.UUID()),
        sa.column('Name', sa.String()),
        sa.column('IsActive', sa.Boolean()),
        sa.column('Version', sa.Integer()),
    )
    op.bulk_insert(roles_table, [
        {"Id": uuid.uuid4(), "Name": "Технический надзор", "IsActive": True, "Version": 1},
        {"Id": uuid.uuid4(), "Name": "Контроль качества", "IsActive": True, "Version": 1},
    ])

    op.add_column('Assignments', sa.Column('RoleOnProjectId', sa.UUID(), nullable=True))

    bind = op.get_bind()
    # "ТН" is this project's established abbreviation for "Технический
    # надзор" (used throughout Employee position names) — map any existing
    # assignments using it to the new canonical role rather than losing data.
    bind.execute(
        sa.text(
            'UPDATE "Assignments" SET "RoleOnProjectId" = '
            '(SELECT "Id" FROM "AssignmentRoles" WHERE "Name" = :canonical) '
            'WHERE "RoleOnProject" = :abbrev'
        ),
        {"canonical": "Технический надзор", "abbrev": "ТН"},
    )

    # Any other pre-existing free-text value is preserved verbatim as a new
    # role rather than silently discarded.
    remaining = bind.execute(
        sa.text(
            'SELECT DISTINCT "RoleOnProject" FROM "Assignments" '
            'WHERE "RoleOnProject" IS NOT NULL AND "RoleOnProjectId" IS NULL'
        )
    ).fetchall()
    for (value,) in remaining:
        new_id = uuid.uuid4()
        bind.execute(
            sa.text(
                'INSERT INTO "AssignmentRoles" ("Id", "Name", "IsActive", "Version") '
                'VALUES (:id, :name, true, 1)'
            ),
            {"id": new_id, "name": value},
        )
        bind.execute(
            sa.text('UPDATE "Assignments" SET "RoleOnProjectId" = :id WHERE "RoleOnProject" = :value'),
            {"id": new_id, "value": value},
        )

    op.create_foreign_key(
        "fk_Assignments_RoleOnProjectId", 'Assignments', 'AssignmentRoles', ['RoleOnProjectId'], ['Id']
    )
    op.drop_column('Assignments', 'RoleOnProject')


def downgrade() -> None:
    op.add_column('Assignments', sa.Column('RoleOnProject', sa.String(length=255), nullable=True))

    bind = op.get_bind()
    bind.execute(
        sa.text(
            'UPDATE "Assignments" a SET "RoleOnProject" = r."Name" '
            'FROM "AssignmentRoles" r WHERE r."Id" = a."RoleOnProjectId"'
        )
    )

    op.drop_constraint("fk_Assignments_RoleOnProjectId", 'Assignments', type_='foreignkey')
    op.drop_column('Assignments', 'RoleOnProjectId')
    op.drop_table('AssignmentRoles')
