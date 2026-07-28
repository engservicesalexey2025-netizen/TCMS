"""initial schema

Revision ID: 8e42a20ef8a3
Revises:
Create Date: 2026-07-21 18:53:41.781251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8e42a20ef8a3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Every AuditMixin table has CreatedBy/ModifiedBy -> Users.Id, while Users
# itself carries EmployeeId -> Employees.Id and its own CreatedBy/ModifiedBy
# -> Users.Id. That's a genuine FK cycle across several tables, so those two
# columns are created here as plain UUID columns and wired up via
# op.create_foreign_key once every table exists, instead of inline
# sa.ForeignKeyConstraint (which requires the target table to already exist).
AUDITED_TABLES = [
    "Employees", "OrgUnits", "Positions", "Roles", "Users",
    "AccessRequests", "Contractors", "Projects", "UserOrgAccess",
    "Assignments", "ConstructionObjects", "Remarks",
]


def upgrade() -> None:
    op.create_table('Employees',
    sa.Column('FullName', sa.String(length=255), nullable=False),
    sa.Column('PositionId', sa.UUID(), nullable=True),
    sa.Column('OrgUnitId', sa.UUID(), nullable=True),
    sa.Column('HireDate', sa.Date(), nullable=True),
    sa.Column('DismissalDate', sa.Date(), nullable=True),
    sa.Column('Status', sa.Enum('ACTIVE', 'DISMISSED', name='employee_status'), nullable=False),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('OrgUnits',
    sa.Column('Name', sa.String(length=255), nullable=False),
    sa.Column('UnitType', sa.Enum('DIVISION', 'DEPARTMENT', 'GROUP', name='org_unit_type'), nullable=False),
    sa.Column('ParentOrgUnitId', sa.UUID(), nullable=True),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['ParentOrgUnitId'], ['OrgUnits.Id'], ),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('Positions',
    sa.Column('Name', sa.String(length=255), nullable=False),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('Id'),
    sa.UniqueConstraint('Name')
    )
    op.create_table('Roles',
    sa.Column('Code', sa.Enum('ADMIN', 'DIVISION_DIRECTOR', 'DEPARTMENT_HEAD', 'GROUP_HEAD', 'OBSERVER', name='role_code'), nullable=False),
    sa.Column('Name', sa.String(length=255), nullable=False),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('Id'),
    sa.UniqueConstraint('Code')
    )
    op.create_table('Users',
    sa.Column('Login', sa.String(length=100), nullable=False),
    sa.Column('Email', sa.String(length=255), nullable=False),
    sa.Column('HashedPassword', sa.String(length=255), nullable=False),
    sa.Column('RoleId', sa.UUID(), nullable=False),
    sa.Column('EmployeeId', sa.UUID(), nullable=True),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['EmployeeId'], ['Employees.Id'], ),
    sa.ForeignKeyConstraint(['RoleId'], ['Roles.Id'], ),
    sa.PrimaryKeyConstraint('Id'),
    sa.UniqueConstraint('Email'),
    sa.UniqueConstraint('Login')
    )
    op.create_table('AccessRequests',
    sa.Column('FullName', sa.String(length=255), nullable=False),
    sa.Column('Email', sa.String(length=255), nullable=False),
    sa.Column('RequestedRoleId', sa.UUID(), nullable=False),
    sa.Column('RequestedOrgUnitId', sa.UUID(), nullable=True),
    sa.Column('Status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='access_request_status'), nullable=False),
    sa.Column('DecidedByUserId', sa.UUID(), nullable=True),
    sa.Column('CreatedUserId', sa.UUID(), nullable=True),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['CreatedUserId'], ['Users.Id'], ),
    sa.ForeignKeyConstraint(['DecidedByUserId'], ['Users.Id'], ),
    sa.ForeignKeyConstraint(['RequestedOrgUnitId'], ['OrgUnits.Id'], ),
    sa.ForeignKeyConstraint(['RequestedRoleId'], ['Roles.Id'], ),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('AuditLog',
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('TableName', sa.String(length=100), nullable=False),
    sa.Column('RecordId', sa.UUID(), nullable=False),
    sa.Column('Action', sa.Enum('CREATE', 'UPDATE', 'ARCHIVE', 'RESTORE', 'EXPORT', 'IMPORT', name='audit_action'), nullable=False),
    sa.Column('ChangedByUserId', sa.UUID(), nullable=True),
    sa.Column('ChangedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('FieldName', sa.String(length=100), nullable=True),
    sa.Column('OldValue', sa.Text(), nullable=True),
    sa.Column('NewValue', sa.Text(), nullable=True),
    sa.Column('IpAddress', sa.String(length=45), nullable=True),
    sa.ForeignKeyConstraint(['ChangedByUserId'], ['Users.Id'], ),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('Contractors',
    sa.Column('Name', sa.String(length=255), nullable=False),
    sa.Column('BinIin', sa.String(length=20), nullable=True),
    sa.Column('ContactInfo', sa.String(length=500), nullable=True),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('Projects',
    sa.Column('Name', sa.String(length=255), nullable=False),
    sa.Column('OrgUnitId', sa.UUID(), nullable=True),
    sa.Column('Area', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('Cost', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('StartDate', sa.Date(), nullable=True),
    sa.Column('EndDate', sa.Date(), nullable=True),
    sa.Column('Status', sa.Enum('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'SUSPENDED', name='project_status'), nullable=False),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['OrgUnitId'], ['OrgUnits.Id'], ),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('UserOrgAccess',
    sa.Column('UserId', sa.UUID(), nullable=False),
    sa.Column('OrgUnitId', sa.UUID(), nullable=False),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['OrgUnitId'], ['OrgUnits.Id'], ),
    sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], ),
    sa.PrimaryKeyConstraint('Id'),
    sa.UniqueConstraint('UserId', 'OrgUnitId')
    )
    op.create_table('Assignments',
    sa.Column('EmployeeId', sa.UUID(), nullable=False),
    sa.Column('ProjectId', sa.UUID(), nullable=False),
    sa.Column('RoleOnProject', sa.String(length=255), nullable=True),
    sa.Column('Workload', sa.Numeric(precision=5, scale=2), nullable=True, comment='Ставка/загрузка, напр. 0.5 = 50%'),
    sa.Column('PeriodStart', sa.Date(), nullable=True),
    sa.Column('PeriodEnd', sa.Date(), nullable=True),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['EmployeeId'], ['Employees.Id'], ),
    sa.ForeignKeyConstraint(['ProjectId'], ['Projects.Id'], ),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('ConstructionObjects',
    sa.Column('ProjectId', sa.UUID(), nullable=False),
    sa.Column('Name', sa.String(length=255), nullable=False),
    sa.Column('Address', sa.String(length=500), nullable=True),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['ProjectId'], ['Projects.Id'], ),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('Remarks',
    sa.Column('ObjectId', sa.UUID(), nullable=False),
    sa.Column('ContractorId', sa.UUID(), nullable=True),
    sa.Column('ResponsibleEmployeeId', sa.UUID(), nullable=True),
    sa.Column('Title', sa.String(length=255), nullable=False),
    sa.Column('Description', sa.Text(), nullable=True),
    sa.Column('Status', sa.Enum('NEW', 'IN_PROGRESS', 'RESOLVED', 'REJECTED', name='remark_status'), nullable=False),
    sa.Column('DueDate', sa.Date(), nullable=True),
    sa.Column('ResolvedDate', sa.Date(), nullable=True),
    sa.Column('Id', sa.UUID(), nullable=False),
    sa.Column('CreatedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('CreatedBy', sa.UUID(), nullable=True),
    sa.Column('ModifiedDate', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ModifiedBy', sa.UUID(), nullable=True),
    sa.Column('IsActive', sa.Boolean(), nullable=False),
    sa.Column('Version', sa.Integer(), nullable=False),
    sa.Column('Comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['ContractorId'], ['Contractors.Id'], ),
    sa.ForeignKeyConstraint(['ObjectId'], ['ConstructionObjects.Id'], ),
    sa.ForeignKeyConstraint(['ResponsibleEmployeeId'], ['Employees.Id'], ),
    sa.PrimaryKeyConstraint('Id')
    )

    # Now that every table exists, wire up the CreatedBy/ModifiedBy audit
    # columns (deferred to break the cycle described above).
    for table in AUDITED_TABLES:
        op.create_foreign_key(
            f"fk_{table}_CreatedBy_Users", table, "Users", ["CreatedBy"], ["Id"]
        )
        op.create_foreign_key(
            f"fk_{table}_ModifiedBy_Users", table, "Users", ["ModifiedBy"], ["Id"]
        )


def downgrade() -> None:
    for table in AUDITED_TABLES:
        op.drop_constraint(f"fk_{table}_ModifiedBy_Users", table, type_="foreignkey")
        op.drop_constraint(f"fk_{table}_CreatedBy_Users", table, type_="foreignkey")

    op.drop_table('Remarks')
    op.drop_table('ConstructionObjects')
    op.drop_table('Assignments')
    op.drop_table('UserOrgAccess')
    op.drop_table('Projects')
    op.drop_table('Contractors')
    op.drop_table('AuditLog')
    op.drop_table('AccessRequests')
    op.drop_table('Users')
    op.drop_table('Roles')
    op.drop_table('Positions')
    op.drop_table('OrgUnits')
    op.drop_table('Employees')
