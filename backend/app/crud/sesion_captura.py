from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SesionCaptura, Calibracion
from app.schemas import SesionCapturaCreate, SesionCapturaUpdate, CalibracionCreate


async def get_sesion(db: AsyncSession, sesion_id: int) -> SesionCaptura | None:
    query = (
        select(SesionCaptura)
        .options(selectinload(SesionCaptura.calibraciones))
        .where(SesionCaptura.id == sesion_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_sesiones_by_observacion(db: AsyncSession, observacion_id: int) -> list[SesionCaptura]:
    query = (
        select(SesionCaptura)
        .options(selectinload(SesionCaptura.calibraciones))
        .where(SesionCaptura.observacion_id == observacion_id)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_sesion(
    db: AsyncSession, observacion_id: int, obj_in: SesionCapturaCreate
) -> SesionCaptura:
    db_sesion = SesionCaptura(**obj_in.model_dump(exclude={"calibraciones", "gain", "offset"}), observacion_id=observacion_id)
    db.add(db_sesion)
    await db.flush()

    for cal_in in obj_in.calibraciones:
        db_cal = Calibracion(**cal_in.model_dump(), sesion_captura_id=db_sesion.id)
        db.add(db_cal)

    await db.commit()
    await db.refresh(db_sesion)
    return await get_sesion(db, db_sesion.id)


async def update_sesion(
    db: AsyncSession, db_sesion: SesionCaptura, obj_in: SesionCapturaUpdate
) -> SesionCaptura:
    update_data = obj_in.model_dump(exclude={"calibraciones"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sesion, field, value)

    if obj_in.calibraciones is not None:
        await db.execute(delete(Calibracion).where(Calibracion.sesion_captura_id == db_sesion.id))
        await db.flush()
        for cal_in in obj_in.calibraciones:
            db_cal = Calibracion(**cal_in.model_dump(), sesion_captura_id=db_sesion.id)
            db.add(db_cal)

    db.add(db_sesion)
    await db.commit()
    await db.refresh(db_sesion)
    return await get_sesion(db, db_sesion.id)


async def delete_sesion(db: AsyncSession, sesion_id: int) -> bool:
    sesion = await get_sesion(db, sesion_id)
    if not sesion:
        return False
    await db.delete(sesion)
    await db.commit()
    return True