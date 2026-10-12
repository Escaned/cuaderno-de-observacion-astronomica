from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Calibracion, TipoCalibracion
from app.schemas import CalibracionCreate, CalibracionUpdate


async def get_calibracion(db: AsyncSession, cal_id: int) -> Calibracion | None:
    result = await db.execute(select(Calibracion).where(Calibracion.id == cal_id))
    return result.scalar_one_or_none()


async def get_calibraciones_by_sesion(db: AsyncSession, sesion_captura_id: int) -> list[Calibracion]:
    result = await db.execute(
        select(Calibracion).where(Calibracion.sesion_captura_id == sesion_captura_id)
    )
    return list(result.scalars().all())


async def create_calibracion(
    db: AsyncSession, sesion_captura_id: int, obj_in: CalibracionCreate
) -> Calibracion:
    db_cal = Calibracion(**obj_in.model_dump(), sesion_captura_id=sesion_captura_id)
    db.add(db_cal)
    await db.commit()
    await db.refresh(db_cal)
    return db_cal


async def update_calibracion(
    db: AsyncSession, db_cal: Calibracion, obj_in: CalibracionUpdate
) -> Calibracion:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cal, field, value)
    db.add(db_cal)
    await db.commit()
    await db.refresh(db_cal)
    return db_cal


async def delete_calibracion(db: AsyncSession, cal_id: int) -> bool:
    cal = await get_calibracion(db, cal_id)
    if not cal:
        return False
    await db.delete(cal)
    await db.commit()
    return True


async def bulk_create_calibraciones(
    db: AsyncSession, sesion_captura_id: int, cals_in: list[CalibracionCreate]
) -> list[Calibracion]:
    db_cals = [
        Calibracion(**cal_in.model_dump(), sesion_captura_id=sesion_captura_id) for cal_in in cals_in
    ]
    db.add_all(db_cals)
    await db.commit()
    for cal in db_cals:
        await db.refresh(cal)
    return db_cals


async def ensure_default_calibraciones(db: AsyncSession, sesion_captura_id: int) -> list[Calibracion]:
    """Ensure all 4 calibration types exist for a session (with count=0 if not provided)."""
    existing = await get_calibraciones_by_sesion(db, sesion_captura_id)
    existing_tipos = {cal.tipo for cal in existing}

    to_create = []
    for tipo in TipoCalibracion:
        if tipo not in existing_tipos:
            to_create.append(
                CalibracionCreate(
                    tipo=tipo,
                    count=0,
                    tiempo_exposicion_seg=None,
                    temperatura=None,
                    filtro_id=None,
                    notas=None,
                )
            )

    if to_create:
        return await bulk_create_calibraciones(db, sesion_captura_id, to_create)
    return existing