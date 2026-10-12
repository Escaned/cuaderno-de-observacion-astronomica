from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Observatorio
from app.schemas import ObservatorioCreate, ObservatorioUpdate


async def get_observatorio(db: AsyncSession) -> Observatorio | None:
    """Get the singleton observatorio (id=1)."""
    result = await db.execute(select(Observatorio).where(Observatorio.id == 1))
    return result.scalar_one_or_none()


async def create_observatorio(db: AsyncSession, obj_in: ObservatorioCreate) -> Observatorio:
    """Create the singleton observatorio."""
    db_obj = Observatorio(**obj_in.model_dump(), id=1)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_observatorio(
    db: AsyncSession, db_obj: Observatorio, obj_in: ObservatorioUpdate
) -> Observatorio:
    """Update the observatorio."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_or_create_observatorio(db: AsyncSession) -> Observatorio:
    """Get existing observatorio or create default from settings."""
    from app.core.config import settings

    obs = await get_observatorio(db)
    if obs:
        return obs

    return await create_observatorio(
        db,
        ObservatorioCreate(
            nombre=settings.obs_nombre,
            latitud=settings.obs_lat,
            longitud=settings.obs_lon,
            altitud_msnm=settings.obs_alt,
            zona_horaria=settings.obs_tz,
        ),
    )