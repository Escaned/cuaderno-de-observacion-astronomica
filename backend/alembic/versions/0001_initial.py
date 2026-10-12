"""Initial migration with seed data

Revision ID: 0001
Revises: 
Create Date: 2026-10-09

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Observatorio table (singleton)
    op.create_table(
        "observatorio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False, server_default="Riguel"),
        sa.Column("latitud", sa.Float(), nullable=False),
        sa.Column("longitud", sa.Float(), nullable=False),
        sa.Column("altitud_msnm", sa.Float(), nullable=True),
        sa.Column("zona_horaria", sa.String(length=50), nullable=False, server_default="Europe/Madrid"),
        sa.CheckConstraint("id = 1", name="ck_observatorio_singleton"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Filtros table
    op.create_table(
        "filtros",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=20), nullable=False),
        sa.Column("descripcion", sa.String(length=200), nullable=True),
        sa.Column("onda_central_nm", sa.Float(), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre", name="uq_filtros_nombre"),
    )

    # Observaciones table
    op.create_table(
        "observaciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("objeto", sa.String(length=100), nullable=False),
        sa.Column("fecha_hora_utc", sa.DateTime(), nullable=False),
        sa.Column("filtro_id", sa.Integer(), nullable=True),
        sa.Column("seeing", sa.Integer(), nullable=False),
        sa.Column("temperatura", sa.Float(), nullable=True),
        sa.Column("humedad", sa.Integer(), nullable=True),
        sa.Column("viento_kph", sa.Float(), nullable=True),
        sa.Column("direccion_viento", sa.String(length=10), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("imagenes", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("actualizado_en", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("seeing BETWEEN 1 AND 5", name="ck_observacion_seeing_range"),
        sa.CheckConstraint("humedad IS NULL OR (humedad >= 0 AND humedad <= 100)", name="ck_observacion_humedad_range"),
        sa.ForeignKeyConstraint(["filtro_id"], ["filtros.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_observaciones_fecha_utc", "observaciones", ["fecha_hora_utc"])
    op.create_index("ix_observaciones_objeto", "observaciones", ["objeto"])
    op.create_index("ix_observaciones_filtro", "observaciones", ["filtro_id"])
    op.create_index("ix_observaciones_fecha_objeto", "observaciones", ["fecha_hora_utc", "objeto"])

    # Sesiones_captura table
    op.create_table(
        "sesiones_captura",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("observacion_id", sa.Integer(), nullable=False),
        sa.Column("filtro_id", sa.Integer(), nullable=False),
        sa.Column("tiempo_exposicion_seg", sa.Float(), nullable=False),
        sa.Column("num_subs", sa.Integer(), nullable=False),
        sa.Column("binning", sa.Integer(), nullable=False, server_default="1"),

        sa.Column("temp_sensor", sa.Float(), nullable=True),
        sa.CheckConstraint("tiempo_exposicion_seg > 0", name="ck_sesion_exposicion_positive"),
        sa.CheckConstraint("num_subs > 0", name="ck_sesion_subs_positive"),
        sa.CheckConstraint("binning >= 1", name="ck_sesion_binning_positive"),
        sa.ForeignKeyConstraint(["observacion_id"], ["observaciones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["filtro_id"], ["filtros.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sesiones_observacion", "sesiones_captura", ["observacion_id"])
    op.create_index("ix_sesiones_filtro", "sesiones_captura", ["filtro_id"])

    # Calibracion table
    op.create_table(
        "calibracion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sesion_captura_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.Enum("dark", "flat", "bias", "darkflat", name="tipocalibracion"), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("tiempo_exposicion_seg", sa.Float(), nullable=True),
        sa.Column("temperatura", sa.Float(), nullable=True),
        sa.Column("filtro_id", sa.Integer(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.CheckConstraint("count >= 0", name="ck_calibracion_count_nonneg"),
        sa.ForeignKeyConstraint(["sesion_captura_id"], ["sesiones_captura.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["filtro_id"], ["filtros.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calibracion_sesion", "calibracion", ["sesion_captura_id"])
    op.create_index("ix_calibracion_tipo", "calibracion", ["tipo"])

    # Seed data: Observatorio
    op.execute(
        """
        INSERT INTO observatorio (id, nombre, latitud, longitud, altitud_msnm, zona_horaria)
        VALUES (1, 'Riguel', 40.4168, -3.7038, 650.0, 'Europe/Madrid')
        ON CONFLICT(id) DO NOTHING
        """
    )

    # Seed data: 6 filtros estándar
    op.execute(
        """
        INSERT INTO filtros (nombre, descripcion, onda_central_nm, orden, activo) VALUES
        ('L', 'Luminancia', NULL, 1, 1),
        ('R', 'Rojo', 656, 2, 1),
        ('G', 'Verde', 540, 3, 1),
        ('B', 'Azul', 450, 4, 1),
        ('Ha', 'H-alpha', 656.3, 5, 1),
        ('OIII', 'Oxigeno III', 500.7, 6, 1)
        ON CONFLICT(nombre) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("calibracion")
    op.drop_table("sesiones_captura")
    op.drop_table("observaciones")
    op.drop_table("filtros")
    op.drop_table("observatorio")