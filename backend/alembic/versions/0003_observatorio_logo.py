"""Observatorio logo

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Logo filename relative to the images directory (served at /imagenes/<logo_path>)
    op.add_column("observatorio", sa.Column("logo_path", sa.String(length=255), nullable=True))

    # Default to the logo bundled with the repo
    op.execute("UPDATE observatorio SET logo_path = 'logo.jpg' WHERE id = 1")


def downgrade() -> None:
    op.drop_column("observatorio", "logo_path")
