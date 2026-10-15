"""Seeing to FWHM (arcseconds)

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add fwhm column with default (SQLite-compatible way)
    with op.batch_alter_table("observaciones") as batch_op:
        batch_op.add_column(sa.Column("fwhm", sa.Float(), nullable=False, server_default="2.5"))
    
    # Backfill fwhm from seeing (rough mapping: 1->5.0, 2->3.5, 3->2.5, 4->1.8, 5->1.2 arcsec)
    op.execute("""
        UPDATE observaciones SET fwhm = CASE seeing
            WHEN 1 THEN 5.0
            WHEN 2 THEN 3.5
            WHEN 3 THEN 2.5
            WHEN 4 THEN 1.8
            WHEN 5 THEN 1.2
            ELSE 2.5
        END
    """)
    
    # Add constraint
    with op.batch_alter_table("observaciones") as batch_op:
        batch_op.create_check_constraint("ck_observacion_fwhm_range", "fwhm >= 0.5 AND fwhm <= 10.0")
        batch_op.drop_constraint("ck_observacion_seeing_range")
        batch_op.drop_column("seeing")


def downgrade() -> None:
    # Add seeing column back with default
    with op.batch_alter_table("observaciones") as batch_op:
        batch_op.add_column(sa.Column("seeing", sa.Integer(), nullable=False, server_default="3"))
    
    # Backfill seeing from fwhm (reverse mapping)
    op.execute("""
        UPDATE observaciones SET seeing = CASE
            WHEN fwhm >= 4.0 THEN 1
            WHEN fwhm >= 3.0 THEN 2
            WHEN fwhm >= 2.0 THEN 3
            WHEN fwhm >= 1.5 THEN 4
            ELSE 5
        END
    """)
    
    # Add constraint and drop fwhm
    with op.batch_alter_table("observaciones") as batch_op:
        batch_op.create_check_constraint("ck_observacion_seeing_range", "seeing BETWEEN 1 AND 5")
        batch_op.drop_constraint("ck_observacion_fwhm_range")
        batch_op.drop_column("fwhm")