from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.crud import (
    get_filtro,
    get_filtro_by_nombre,
    get_filtros,
    count_filtros,
    create_filtro,
    update_filtro,
    delete_filtro,
    reorder_filtros,
)
from app.schemas import FiltroCreate, FiltroUpdate, FiltroRead, FiltroReorder

router = APIRouter()


@router.get("", response_model=list[FiltroRead])
async def read_filtros(
    skip: int = 0,
    limit: int = 100,
    activo_only: bool = False,
    db: AsyncSession = Depends(get_session),
):
    """Get all filtros."""
    return await get_filtros(db, skip=skip, limit=limit, activo_only=activo_only)


@router.get("/count", response_model=int)
async def count_filtros_endpoint(
    activo_only: bool = False, db: AsyncSession = Depends(get_session)
):
    """Count filtros."""
    return await count_filtros(db, activo_only=activo_only)


@router.get("/{filtro_id}", response_model=FiltroRead)
async def read_filtro(filtro_id: int, db: AsyncSession = Depends(get_session)):
    """Get a specific filtro by ID."""
    filtro = await get_filtro(db, filtro_id)
    if not filtro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filtro not found")
    return filtro


@router.post("", response_model=FiltroRead, status_code=status.HTTP_201_CREATED)
async def create_filtro_endpoint(obj_in: FiltroCreate, db: AsyncSession = Depends(get_session)):
    """Create a new filtro."""
    existing = await get_filtro_by_nombre(db, obj_in.nombre)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Filtro with this name already exists"
        )
    return await create_filtro(db, obj_in)


@router.put("/{filtro_id}", response_model=FiltroRead)
async def update_filtro_endpoint(
    filtro_id: int, obj_in: FiltroUpdate, db: AsyncSession = Depends(get_session)
):
    """Update a filtro."""
    filtro = await get_filtro(db, filtro_id)
    if not filtro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filtro not found")

    if obj_in.nombre and obj_in.nombre != filtro.nombre:
        existing = await get_filtro_by_nombre(db, obj_in.nombre)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filtro with this name already exists",
            )

    return await update_filtro(db, filtro, obj_in)


@router.delete("/{filtro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filtro_endpoint(filtro_id: int, db: AsyncSession = Depends(get_session)):
    """Delete a filtro."""
    success = await delete_filtro(db, filtro_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filtro not found")


@router.post("/reorder", response_model=list[FiltroRead])
async def reorder_filtros_endpoint(
    reorders: list[FiltroReorder], db: AsyncSession = Depends(get_session)
):
    """Reorder filtros."""
    return await reorder_filtros(db, reorders)