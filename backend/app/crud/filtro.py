from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Filtro
from app.schemas import FiltroCreate, FiltroUpdate, FiltroReorder


async def get_filtro(db: AsyncSession, filtro_id: int) -> Filtro | None:
    result = await db.execute(select(Filtro).where(Filtro.id == filtro_id))
    return result.scalar_one_or_none()


async def get_filtro_by_nombre(db: AsyncSession, nombre: str) -> Filtro | None:
    result = await db.execute(select(Filtro).where(Filtro.nombre == nombre))
    return result.scalar_one_or_none()


async def get_filtros(
    db: AsyncSession, *, skip: int = 0, limit: int = 100, activo_only: bool = False
) -> list[Filtro]:
    query = select(Filtro).order_by(Filtro.orden, Filtro.id)
    if activo_only:
        query = query.where(Filtro.activo.is_(True))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_filtros(db: AsyncSession, *, activo_only: bool = False) -> int:
    query = select(func.count(Filtro.id))
    if activo_only:
        query = query.where(Filtro.activo.is_(True))
    result = await db.execute(query)
    return result.scalar_one()


async def create_filtro(db: AsyncSession, obj_in: FiltroCreate) -> Filtro:
    db_obj = Filtro(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_filtro(db: AsyncSession, db_obj: Filtro, obj_in: FiltroUpdate) -> Filtro:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_filtro(db: AsyncSession, filtro_id: int) -> bool:
    filtro = await get_filtro(db, filtro_id)
    if not filtro:
        return False
    await db.delete(filtro)
    await db.commit()
    return True


async def reorder_filtros(db: AsyncSession, reorders: list[FiltroReorder]) -> list[Filtro]:
    for reorder in reorders:
        filtro = await get_filtro(db, reorder.filtro_id)
        if filtro:
            filtro.orden = reorder.orden
            db.add(filtro)
    await db.commit()
    return await get_filtros(db)