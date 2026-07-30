"""additional workload norms

Revision ID: f3af66a01481
Revises: 1e71170ea9b3
Create Date: 2026-07-28 22:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3af66a01481'
down_revision: Union[str, None] = '1e71170ea9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_LINK_CENTER_ON_SITE = (
    "https://docs.google.com/spreadsheets/d/1ljslAcZx0AOCDRBIFs76yfzrRv7hDNlS-"
    "xFhyJJsbdo/edit?gid=1721426694#gid=1721426694"
)
_LINK_CENTER_K2 = (
    "https://docs.google.com/spreadsheets/d/1ljslAcZx0AOCDRBIFs76yfzrRv7hDNlS-"
    "xFhyJJsbdo/edit?gid=854470560#gid=854470560"
)
_LINK_CENTER_DF = (
    "https://docs.google.com/spreadsheets/d/1ljslAcZx0AOCDRBIFs76yfzrRv7hDNlS-"
    "xFhyJJsbdo/edit?usp=sharing"
)

# Category, NormValue, SignalValue, LimitValue, Coefficient, MetricLinkUrl
# — Раздел 2 (Таблица 1) и Разделы 4.1-4.2 регламента BIG-HRM-RGL-038-RU.
ROWS = [
    ("GENERAL_CONSTRUCTION_ENGINEER", 46000, 69000, 92000, 0.3, None),
    ("UTILITY_NETWORKS_ENGINEER", 250000, 300000, 400000, 0.4, None),
    ("GROUP_DIVISION_HEAD_ON_SITE_CENTER", 600000, None, 1200000, None, _LINK_CENTER_ON_SITE),
    ("GROUP_HEAD_K2_CENTER", 300000, None, 600000, None, _LINK_CENTER_K2),
    ("GROUP_DIVISION_HEAD_EXTERNAL_CENTER", 400000, None, 800000, None, _LINK_CENTER_ON_SITE),
    ("BRANCH_DIRECTOR_K2_CENTER", 1200000, None, 2400000, None, _LINK_CENTER_DF),
    ("BRANCH_DIRECTOR_K2_EXTERNAL_CENTER", 1000000, None, 2000000, None, _LINK_CENTER_DF),
    ("GROUP_HEAD_ALMATY_SHYMKENT", 400000, None, 800000, None, None),
    ("DIVISION_HEAD_ALMATY_SHYMKENT", 600000, None, 1200000, None, None),
    ("BRANCH_DIRECTOR_ALMATY_SHYMKENT", 1200000, None, 2400000, None, None),
]


def upgrade() -> None:
    workload_category_enum = sa.Enum(
        "GENERAL_CONSTRUCTION_ENGINEER", "UTILITY_NETWORKS_ENGINEER",
        "GROUP_DIVISION_HEAD_ON_SITE_CENTER", "GROUP_HEAD_K2_CENTER",
        "GROUP_DIVISION_HEAD_EXTERNAL_CENTER", "BRANCH_DIRECTOR_K2_CENTER",
        "BRANCH_DIRECTOR_K2_EXTERNAL_CENTER", "GROUP_HEAD_ALMATY_SHYMKENT",
        "DIVISION_HEAD_ALMATY_SHYMKENT", "BRANCH_DIRECTOR_ALMATY_SHYMKENT",
        name="workload_category",
    )
    # Type created implicitly by op.create_table below (fresh table+type).

    op.create_table(
        'AdditionalWorkloadNorms',
        sa.Column('Category', workload_category_enum, nullable=False),
        sa.Column('NormValue', sa.Integer(), nullable=False),
        sa.Column('SignalValue', sa.Integer(), nullable=True),
        sa.Column('LimitValue', sa.Integer(), nullable=False),
        sa.Column('Coefficient', sa.Numeric(5, 4), nullable=True),
        sa.Column('MetricLinkUrl', sa.String(length=1000), nullable=True),
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
        sa.UniqueConstraint('Category'),
    )

    table = sa.table(
        'AdditionalWorkloadNorms',
        sa.column('Id', sa.UUID()),
        sa.column('Category', workload_category_enum),
        sa.column('NormValue', sa.Integer()),
        sa.column('SignalValue', sa.Integer()),
        sa.column('LimitValue', sa.Integer()),
        sa.column('Coefficient', sa.Numeric(5, 4)),
        sa.column('MetricLinkUrl', sa.String(1000)),
        sa.column('IsActive', sa.Boolean()),
        sa.column('Version', sa.Integer()),
    )
    op.bulk_insert(table, [
        {
            "Id": uuid.uuid4(),
            "Category": category,
            "NormValue": norm,
            "SignalValue": signal,
            "LimitValue": limit,
            "Coefficient": coefficient,
            "MetricLinkUrl": link,
            "IsActive": True,
            "Version": 1,
        }
        for category, norm, signal, limit, coefficient, link in ROWS
    ])


def downgrade() -> None:
    op.drop_table('AdditionalWorkloadNorms')
    sa.Enum(name='workload_category').drop(op.get_bind(), checkfirst=True)
