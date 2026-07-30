"""kpi coefficients

Revision ID: 1e71170ea9b3
Revises: 75faf68122fc
Create Date: 2026-07-28 21:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1e71170ea9b3'
down_revision: Union[str, None] = '75faf68122fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Норма предписаний / инспекций по паре «тип объекта × стадия» — Раздел 6
# методики оценки эффективности технадзора. Порядок типов в каждой строке:
# Жилое, Обществ., Промышл., Линейный, Инж. сети.
OBJECT_CATEGORIES = ["RESIDENTIAL", "PUBLIC", "INDUSTRIAL", "LINEAR", "UTILITY_NETWORKS"]

PRESCRIPTION_NORMS = {
    "EARTHWORKS": [8, 9, 11, 10, 9],
    "MONOLITH_FRAME": [15, 16, 18, 10, 8],
    "FACADE_ROOF": [10, 12, 9, 4, 3],
    "MEP": [12, 14, 16, 12, 15],
    "FINISHING": [9, 11, 7, 3, 4],
    "COMMISSIONING": [6, 7, 10, 8, 9],
}

INSPECTION_NORMS = {
    "EARTHWORKS": [12, 12, 16, 14, 12],
    "MONOLITH_FRAME": [20, 20, 24, 12, 10],
    "FACADE_ROOF": [14, 16, 12, 6, 5],
    "MEP": [16, 18, 20, 16, 20],
    "FINISHING": [12, 14, 10, 5, 6],
    "COMMISSIONING": [8, 10, 14, 10, 12],
}


def upgrade() -> None:
    object_category_enum = sa.Enum(
        "RESIDENTIAL", "PUBLIC", "INDUSTRIAL", "LINEAR", "UTILITY_NETWORKS",
        name="kpi_object_category",
    )
    supervision_stage_enum = sa.Enum(
        "EARTHWORKS", "MONOLITH_FRAME", "FACADE_ROOF", "MEP", "FINISHING", "COMMISSIONING",
        name="kpi_supervision_stage",
    )
    metric_type_enum = sa.Enum("PRESCRIPTIONS", "INSPECTIONS", name="kpi_metric_type")
    # Types are created implicitly by op.create_table below (fresh types on a
    # fresh table, unlike the op.add_column case elsewhere in this project
    # which requires an explicit .create() since ADD COLUMN doesn't do it).

    op.create_table(
        'KpiNormMatrix',
        sa.Column('ObjectCategory', object_category_enum, nullable=False),
        sa.Column('Stage', supervision_stage_enum, nullable=False),
        sa.Column('MetricType', metric_type_enum, nullable=False),
        sa.Column('NormValue', sa.Integer(), nullable=False),
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
        sa.UniqueConstraint('ObjectCategory', 'Stage', 'MetricType', name='uq_KpiNormMatrix_cell'),
    )

    op.create_table(
        'KpiSettings',
        sa.Column('WeightKpi', sa.Numeric(5, 4), nullable=False),
        sa.Column('WeightIqc', sa.Numeric(5, 4), nullable=False),
        sa.Column('WeightCri', sa.Numeric(5, 4), nullable=False),
        sa.Column('WeightS1', sa.Numeric(5, 4), nullable=False),
        sa.Column('WeightS2', sa.Numeric(5, 4), nullable=False),
        sa.Column('WeightS3', sa.Numeric(5, 4), nullable=False),
        sa.Column('WeightS4', sa.Numeric(5, 4), nullable=False),
        sa.Column('WeightDiversity', sa.Numeric(6, 4), nullable=False),
        sa.Column('WeightNormative', sa.Numeric(6, 4), nullable=False),
        sa.Column('WeightTechnical', sa.Numeric(6, 4), nullable=False),
        sa.Column('CriTarget', sa.Numeric(5, 4), nullable=False),
        sa.Column('CategoryExcellentMin', sa.Numeric(5, 2), nullable=False),
        sa.Column('CategoryGoodMin', sa.Numeric(5, 2), nullable=False),
        sa.Column('CategorySatisfactoryMin', sa.Numeric(5, 2), nullable=False),
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
    )

    norm_matrix_table = sa.table(
        'KpiNormMatrix',
        sa.column('Id', sa.UUID()),
        sa.column('ObjectCategory', object_category_enum),
        sa.column('Stage', supervision_stage_enum),
        sa.column('MetricType', metric_type_enum),
        sa.column('NormValue', sa.Integer()),
        sa.column('IsActive', sa.Boolean()),
        sa.column('Version', sa.Integer()),
    )
    rows = []
    for metric_type, norms in (("PRESCRIPTIONS", PRESCRIPTION_NORMS), ("INSPECTIONS", INSPECTION_NORMS)):
        for stage, values in norms.items():
            for category, value in zip(OBJECT_CATEGORIES, values):
                rows.append({
                    "Id": uuid.uuid4(),
                    "ObjectCategory": category,
                    "Stage": stage,
                    "MetricType": metric_type,
                    "NormValue": value,
                    "IsActive": True,
                    "Version": 1,
                })
    op.bulk_insert(norm_matrix_table, rows)

    settings_table = sa.table(
        'KpiSettings',
        sa.column('Id', sa.UUID()),
        sa.column('WeightKpi', sa.Numeric(5, 4)),
        sa.column('WeightIqc', sa.Numeric(5, 4)),
        sa.column('WeightCri', sa.Numeric(5, 4)),
        sa.column('WeightS1', sa.Numeric(5, 4)),
        sa.column('WeightS2', sa.Numeric(5, 4)),
        sa.column('WeightS3', sa.Numeric(5, 4)),
        sa.column('WeightS4', sa.Numeric(5, 4)),
        sa.column('WeightDiversity', sa.Numeric(6, 4)),
        sa.column('WeightNormative', sa.Numeric(6, 4)),
        sa.column('WeightTechnical', sa.Numeric(6, 4)),
        sa.column('CriTarget', sa.Numeric(5, 4)),
        sa.column('CategoryExcellentMin', sa.Numeric(5, 2)),
        sa.column('CategoryGoodMin', sa.Numeric(5, 2)),
        sa.column('CategorySatisfactoryMin', sa.Numeric(5, 2)),
        sa.column('IsActive', sa.Boolean()),
        sa.column('Version', sa.Integer()),
    )
    op.bulk_insert(settings_table, [{
        "Id": uuid.uuid4(),
        "WeightKpi": 0.50, "WeightIqc": 0.35, "WeightCri": 0.15,
        "WeightS1": 0.30, "WeightS2": 0.20, "WeightS3": 0.20, "WeightS4": 0.30,
        "WeightDiversity": 0.2857, "WeightNormative": 0.4286, "WeightTechnical": 0.2857,
        "CriTarget": 0.30,
        "CategoryExcellentMin": 85, "CategoryGoodMin": 70, "CategorySatisfactoryMin": 55,
        "IsActive": True, "Version": 1,
    }])


def downgrade() -> None:
    op.drop_table('KpiSettings')
    op.drop_table('KpiNormMatrix')
    sa.Enum(name='kpi_metric_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='kpi_supervision_stage').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='kpi_object_category').drop(op.get_bind(), checkfirst=True)
