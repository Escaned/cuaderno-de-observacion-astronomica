from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asociacion
from app.schemas import AsociacionUpdate


async def get_asociacion(db: AsyncSession) -> Asociacion | None:
    """Get the singleton asociacion (id=1)."""
    result = await db.execute(select(Asociacion).where(Asociacion.id == 1))
    return result.scalar_one_or_none()


async def update_asociacion(
    db: AsyncSession, db_obj: Asociacion, obj_in: AsociacionUpdate
) -> Asociacion:
    """Update the asociacion."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_or_create_asociacion(db: AsyncSession) -> Asociacion:
    """Get the asociacion or create it from the configured defaults."""
    from app.core.config import settings

    asociacion = await get_asociacion(db)
    if asociacion:
        return asociacion

    db_obj = Asociacion(id=1, nombre=settings.obs_nombre, logo_path="logo.jpg")
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
