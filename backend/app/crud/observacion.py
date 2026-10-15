from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.models import Observacion, SesionCaptura, Calibracion, Filtro, TipoCalibracion
from app.schemas import ObservacionCreate, ObservacionUpdate, SesionCapturaCreate, CalibracionCreate


async def get_observacion(db: AsyncSession, observacion_id: int) -> Observacion | None:
    query = (
        select(Observacion)
        .options(
            selectinload(Observacion.sesiones_captura).selectinload(SesionCaptura.calibraciones),
            selectinload(Observacion.filtro),
        )
        .where(Observacion.id == observacion_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_observaciones(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    filtro_id: Optional[int] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    objeto: Optional[str] = None,
) -> list[Observacion]:
    query = (
        select(Observacion)
        .options(
            selectinload(Observacion.sesiones_captura).selectinload(SesionCaptura.calibraciones),
            selectinload(Observacion.filtro),
        )
        .order_by(Observacion.fecha_hora_utc.desc())
    )
    if filtro_id:
        query = query.where(Observacion.filtro_id == filtro_id)
    if fecha_desde:
        query = query.where(Observacion.fecha_hora_utc >= fecha_desde)
    if fecha_hasta:
        query = query.where(Observacion.fecha_hora_utc <= fecha_hasta)
    if objeto:
        query = query.where(Observacion.objeto.ilike(f"%{objeto}%"))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_observaciones(
    db: AsyncSession,
    *,
    filtro_id: Optional[int] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    objeto: Optional[str] = None,
) -> int:
    query = select(func.count(Observacion.id))
    if filtro_id:
        query = query.where(Observacion.filtro_id == filtro_id)
    if fecha_desde:
        query = query.where(Observacion.fecha_hora_utc >= fecha_desde)
    if fecha_hasta:
        query = query.where(Observacion.fecha_hora_utc <= fecha_hasta)
    if objeto:
        query = query.where(Observacion.objeto.ilike(f"%{objeto}%"))
    result = await db.execute(query)
    return result.scalar_one()


async def create_observacion(db: AsyncSession, obj_in: ObservacionCreate) -> Observacion:
    # Create observacion
    obs_data = obj_in.model_dump(exclude={"sesiones_captura"})
    db_obs = Observacion(**obs_data)
    db.add(db_obs)
    await db.flush()

    # Create sesiones_captura with calibraciones
    for sesion_in in obj_in.sesiones_captura:
        sesion_data = sesion_in.model_dump(exclude={"calibraciones"})
        db_sesion = SesionCaptura(**sesion_data, observacion_id=db_obs.id)
        db.add(db_sesion)
        await db.flush()

        for cal_in in sesion_in.calibraciones:
            db_cal = Calibracion(**cal_in.model_dump(), sesion_captura_id=db_sesion.id)
            db.add(db_cal)

    await db.commit()
    await db.refresh(db_obs)
    return await get_observacion(db, db_obs.id)


async def update_observacion(
    db: AsyncSession, db_obs: Observacion, obj_in: ObservacionUpdate
) -> Observacion:
    # Update observacion fields
    update_data = obj_in.model_dump(exclude={"sesiones_captura"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obs, field, value)

    # Handle sesiones_captura replacement if provided
    if obj_in.sesiones_captura is not None:
        # Delete existing sesiones and their calibraciones (cascade handles calibraciones)
        await db.execute(
            delete(SesionCaptura).where(SesionCaptura.observacion_id == db_obs.id)
        )
        await db.flush()

        # Expire the relationship collection so SQLAlchemy doesn't try to cascade to deleted objects
        db.expire(db_obs, ["sesiones_captura"])

        # Create new sesiones
        for sesion_in in obj_in.sesiones_captura:
            sesion_data = sesion_in.model_dump(exclude={"calibraciones"})
            db_sesion = SesionCaptura(**sesion_data, observacion_id=db_obs.id)
            db.add(db_sesion)
            await db.flush()

            for cal_in in sesion_in.calibraciones:
                db_cal = Calibracion(**cal_in.model_dump(), sesion_captura_id=db_sesion.id)
                db.add(db_cal)

    db.add(db_obs)
    await db.commit()
    await db.refresh(db_obs)
    return await get_observacion(db, db_obs.id)


async def duplicate_observacion(db: AsyncSession, observacion_id: int) -> Observacion:
    original = await get_observacion(db, observacion_id)
    if not original:
        raise ValueError("Observacion not found")

    # Create new observacion with copied data
    new_obs = Observacion(
        objeto=original.objeto,
        fecha_hora_utc=original.fecha_hora_utc,
        filtro_id=original.filtro_id,
        fwhm=original.fwhm,
        temperatura=original.temperatura,
        humedad=original.humedad,
        viento_kph=original.viento_kph,
        direccion_viento=original.direccion_viento,
        descripcion=original.descripcion,
        imagenes=original.imagenes,
    )
    db.add(new_obs)
    await db.flush()

    # Copy sesiones_captura and calibraciones
    for sesion in original.sesiones_captura:
        new_sesion = SesionCaptura(
            observacion_id=new_obs.id,
            filtro_id=sesion.filtro_id,
            tiempo_exposicion_seg=sesion.tiempo_exposicion_seg,
            num_subs=sesion.num_subs,
            binning=sesion.binning,
            temp_sensor=sesion.temp_sensor,
        )
        db.add(new_sesion)
        await db.flush()

        for cal in sesion.calibraciones:
            new_cal = Calibracion(
                sesion_captura_id=new_sesion.id,
                tipo=cal.tipo,
                count=cal.count,
                tiempo_exposicion_seg=cal.tiempo_exposicion_seg,
                temperatura=cal.temperatura,
                filtro_id=cal.filtro_id,
                notas=cal.notas,
            )
            db.add(new_cal)

    await db.commit()
    await db.refresh(new_obs)
    return await get_observacion(db, new_obs.id)


async def delete_observacion(db: AsyncSession, observacion_id: int) -> bool:
    obs = await get_observacion(db, observacion_id)
    if not obs:
        return False
    await db.delete(obs)
    await db.commit()
    return True