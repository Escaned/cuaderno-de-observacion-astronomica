import csv
import io
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Observacion, SesionCaptura, Calibracion, Filtro, Asociacion, Observatorio


async def generate_csv_export(
    db: AsyncSession,
    tabla: str = "all",
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    filtro_id: Optional[int] = None,
) -> bytes:
    """Generate CSV export as bytes. When tabla='all', combines all tables into a single CSV with section headers."""
    output = io.StringIO()
    writer = csv.writer(output)

    if tabla == "all":
        # All tables combined into one CSV with section headers
        await _write_asociacion(writer, db)
        writer.writerow([])
        await _write_observatorios(writer, db)
        writer.writerow([])
        await _write_filtros(writer, db)
        writer.writerow([])
        await _write_observaciones(writer, db, fecha_desde, fecha_hasta, filtro_id)
        writer.writerow([])
        await _write_sesiones(writer, db, fecha_desde, fecha_hasta, filtro_id)
        writer.writerow([])
        await _write_calibraciones(writer, db, fecha_desde, fecha_hasta, filtro_id)
    elif tabla == "observaciones":
        await _write_observaciones(writer, db, fecha_desde, fecha_hasta, filtro_id)
    elif tabla == "sesiones_captura":
        await _write_sesiones(writer, db, fecha_desde, fecha_hasta, filtro_id)
    elif tabla == "calibracion":
        await _write_calibraciones(writer, db, fecha_desde, fecha_hasta, filtro_id)
    elif tabla == "filtros":
        await _write_filtros(writer, db)
    elif tabla == "asociacion":
        await _write_asociacion(writer, db)
    elif tabla in ("observatorios", "observatorio"):
        await _write_observatorios(writer, db)

    return output.getvalue().encode("utf-8")


async def _write_asociacion(writer, db):
    writer.writerow(["=== ASOCIACION ==="])
    writer.writerow(["id", "nombre", "logo_path"])
    result = await db.execute(select(Asociacion))
    for asociacion in result.scalars().all():
        writer.writerow([asociacion.id, asociacion.nombre, asociacion.logo_path])


async def _write_observatorios(writer, db):
    writer.writerow(["=== OBSERVATORIOS ==="])
    writer.writerow([
        "id", "nombre", "latitud", "longitud", "altitud_msnm",
        "zona_horaria", "color", "es_predeterminado",
    ])
    result = await db.execute(
        select(Observatorio).order_by(Observatorio.es_predeterminado.desc(), Observatorio.nombre)
    )
    for obs in result.scalars().all():
        writer.writerow([
            obs.id, obs.nombre, obs.latitud, obs.longitud, obs.altitud_msnm,
            obs.zona_horaria, obs.color, obs.es_predeterminado,
        ])


async def _write_filtros(writer, db):
    writer.writerow(["=== FILTROS ==="])
    writer.writerow(["id", "nombre", "descripcion", "onda_central_nm", "orden", "activo"])
    result = await db.execute(select(Filtro).order_by(Filtro.orden, Filtro.id))
    for filtro in result.scalars().all():
        writer.writerow([
            filtro.id, filtro.nombre, filtro.descripcion, filtro.onda_central_nm,
            filtro.orden, filtro.activo
        ])


async def _write_observaciones(writer, db, fecha_desde, fecha_hasta, filtro_id):
    writer.writerow(["=== OBSERVACIONES ==="])
    writer.writerow([
        "id", "objeto", "fecha_hora_utc", "observatorio_id", "observatorio_nombre",
        "filtro_id", "filtro_nombre",
        "fwhm_arcsec", "temperatura", "humedad", "viento_kph", "direccion_viento",
        "descripcion", "imagenes", "creado_en", "actualizado_en"
    ])
    query = (
        select(Observacion)
        .options(selectinload(Observacion.filtro), selectinload(Observacion.observatorio))
        .order_by(Observacion.fecha_hora_utc.desc())
    )
    if fecha_desde:
        query = query.where(Observacion.fecha_hora_utc >= fecha_desde)
    if fecha_hasta:
        query = query.where(Observacion.fecha_hora_utc <= fecha_hasta)
    if filtro_id:
        query = query.where(Observacion.filtro_id == filtro_id)
    result = await db.execute(query)
    for obs in result.scalars().all():
        writer.writerow([
            obs.id, obs.objeto, obs.fecha_hora_utc.isoformat(),
            obs.observatorio_id, obs.observatorio.nombre if obs.observatorio else None,
            obs.filtro_id, obs.filtro.nombre if obs.filtro else None,
            obs.fwhm, obs.temperatura,
            obs.humedad, obs.viento_kph, obs.direccion_viento, obs.descripcion,
            obs.imagenes, obs.creado_en.isoformat(), obs.actualizado_en.isoformat()
        ])


async def _write_sesiones(writer, db, fecha_desde, fecha_hasta, filtro_id):
    writer.writerow(["=== SESIONES_CAPTURA ==="])
    writer.writerow([
        "id", "observacion_id", "objeto", "fecha_hora_utc", "filtro_id", "filtro_nombre",
        "tiempo_exposicion_seg", "num_subs", "total_tiempo_seg", "binning", "temp_sensor"
    ])
    query = (
        select(SesionCaptura)
        .join(Observacion)
        .options(selectinload(SesionCaptura.filtro), selectinload(SesionCaptura.observacion))
        .order_by(Observacion.fecha_hora_utc.desc())
    )
    if fecha_desde:
        query = query.where(Observacion.fecha_hora_utc >= fecha_desde)
    if fecha_hasta:
        query = query.where(Observacion.fecha_hora_utc <= fecha_hasta)
    if filtro_id:
        query = query.where(SesionCaptura.filtro_id == filtro_id)
    result = await db.execute(query)
    for sesion in result.scalars().all():
        writer.writerow([
            sesion.id, sesion.observacion_id, sesion.observacion.objeto,
            sesion.observacion.fecha_hora_utc.isoformat(), sesion.filtro_id,
            sesion.filtro.nombre if sesion.filtro else None,
            sesion.tiempo_exposicion_seg, sesion.num_subs, sesion.total_tiempo_seg,
            sesion.binning, sesion.temp_sensor
        ])


async def _write_calibraciones(writer, db, fecha_desde, fecha_hasta, filtro_id):
    writer.writerow(["=== CALIBRACION ==="])
    writer.writerow([
        "id", "sesion_captura_id", "observacion_id", "objeto", "fecha_hora_utc",
        "tipo", "count", "tiempo_exposicion_seg", "temperatura", "filtro_id", "filtro_nombre", "notas"
    ])
    query = (
        select(Calibracion)
        .join(SesionCaptura)
        .join(Observacion)
        .options(
            selectinload(Calibracion.sesion_captura).selectinload(SesionCaptura.observacion),
            selectinload(Calibracion.filtro),
        )
        .order_by(Observacion.fecha_hora_utc.desc())
    )
    if fecha_desde:
        query = query.where(Observacion.fecha_hora_utc >= fecha_desde)
    if fecha_hasta:
        query = query.where(Observacion.fecha_hora_utc <= fecha_hasta)
    if filtro_id:
        query = query.where(Calibracion.filtro_id == filtro_id)
    result = await db.execute(query)
    for cal in result.scalars().all():
        writer.writerow([
            cal.id, cal.sesion_captura_id, cal.sesion_captura.observacion_id,
            cal.sesion_captura.observacion.objeto, cal.sesion_captura.observacion.fecha_hora_utc.isoformat(),
            cal.tipo.value, cal.count, cal.tiempo_exposicion_seg, cal.temperatura,
            cal.filtro_id, cal.filtro.nombre if cal.filtro else None, cal.notas
        ])