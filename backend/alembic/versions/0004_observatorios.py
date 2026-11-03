"""Asociacion separada de los observatorios (varios observatorios)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-03

Antes habia un unico observatorio que hacia de asociacion. Ahora la asociacion
guarda solo su nombre y su logo, y cada observatorio es una fila propia con
nombre, coordenadas, altitud y color. Las observaciones existentes se asignan al
observatorio que ya estaba configurado.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # La asociacion (nombre y logo) deja de vivir en la fila del observatorio.
    op.create_table(
        "asociacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False, server_default="Riguel"),
        sa.Column("logo_path", sa.String(length=255), nullable=True),
        sa.CheckConstraint("id = 1", name="ck_asociacion_singleton"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO asociacion (id, nombre, logo_path)
        SELECT 1, nombre, logo_path FROM observatorio WHERE id = 1
        """
    )

    # El observatorio deja de ser unico y gana color y marca de predeterminado.
    op.create_table(
        "observatorio_nuevo",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("nombre", sa.String(length=100), nullable=False, server_default="Riguel"),
        sa.Column("latitud", sa.Float(), nullable=False),
        sa.Column("longitud", sa.Float(), nullable=False),
        sa.Column("altitud_msnm", sa.Float(), nullable=True),
        sa.Column("zona_horaria", sa.String(length=50), nullable=False, server_default="Europe/Madrid"),
        sa.Column("color", sa.String(length=7), nullable=False, server_default="#4d48e2"),
        sa.Column("es_predeterminado", sa.Boolean(), nullable=False, server_default="0"),
        sa.CheckConstraint("latitud >= -90 AND latitud <= 90", name="ck_observatorio_latitud_range"),
        sa.CheckConstraint("longitud >= -180 AND longitud <= 180", name="ck_observatorio_longitud_range"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO observatorio_nuevo
            (id, nombre, latitud, longitud, altitud_msnm, zona_horaria, color, es_predeterminado)
        SELECT id, nombre, latitud, longitud, altitud_msnm, zona_horaria, '#4d48e2', 1
        FROM observatorio
        """
    )
    op.drop_table("observatorio")
    op.rename_table("observatorio_nuevo", "observatorio")

    # Cada observacion queda asociada al observatorio activo hasta ahora.
    # SQLite no permite agregar una FK con ALTER TABLE, asi que la tabla se
    # reconstruye en modo batch.
    with op.batch_alter_table("observaciones") as batch_op:
        batch_op.add_column(sa.Column("observatorio_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_observaciones_observatorio",
            "observatorio",
            ["observatorio_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_observaciones_observatorio", ["observatorio_id"])
    op.execute(
        """
        UPDATE observaciones
        SET observatorio_id = (SELECT id FROM observatorio ORDER BY id LIMIT 1)
        WHERE observatorio_id IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("observaciones") as batch_op:
        batch_op.drop_index("ix_observaciones_observatorio")
        batch_op.drop_constraint("fk_observaciones_observatorio", type_="foreignkey")
        batch_op.drop_column("observatorio_id")

    op.create_table(
        "observatorio_viejo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False, server_default="Riguel"),
        sa.Column("latitud", sa.Float(), nullable=False),
        sa.Column("longitud", sa.Float(), nullable=False),
        sa.Column("altitud_msnm", sa.Float(), nullable=True),
        sa.Column("zona_horaria", sa.String(length=50), nullable=False, server_default="Europe/Madrid"),
        sa.Column("logo_path", sa.String(length=255), nullable=True),
        sa.CheckConstraint("id = 1", name="ck_observatorio_singleton"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO observatorio_viejo
            (id, nombre, latitud, longitud, altitud_msnm, zona_horaria, logo_path)
        SELECT 1, o.nombre, o.latitud, o.longitud, o.altitud_msnm, o.zona_horaria, a.logo_path
        FROM observatorio o
        LEFT JOIN asociacion a ON a.id = 1
        ORDER BY o.es_predeterminado DESC, o.id ASC
        LIMIT 1
        """
    )
    op.drop_table("observatorio")
    op.rename_table("observatorio_viejo", "observatorio")
    op.drop_table("asociacion")
