from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.core.database import get_session
from app.crud import (
    get_observacion,
    get_observaciones,
    count_observaciones,
    create_observacion,
    update_observacion,
    duplicate_observacion,
    delete_observacion,
)
from app.schemas import ObservacionCreate, ObservacionUpdate, ObservacionRead, ObservacionListItem

router = APIRouter()


@router.get("/stats")
async def get_observaciones_stats(db: AsyncSession = Depends(get_session)):
    """Get total exposure time across all observations."""
    from sqlalchemy import select, func
    from app.models import SesionCaptura
    query = select(func.coalesce(func.sum(SesionCaptura.tiempo_exposicion_seg * SesionCaptura.num_subs), 0))
    result = await db.execute(query)
    total = result.scalar_one()
    return {"total_exposicion_seg": total}


@router.get("/count", response_model=int)
async def count_observaciones_endpoint(
    filtro_id: Optional[int] = None,
    observatorio_id: Optional[int] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    objeto: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    """Count observaciones with optional filters."""
    return await count_observaciones(
        db,
        filtro_id=filtro_id,
        observatorio_id=observatorio_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        objeto=objeto,
    )


@router.get("", response_model=list[ObservacionListItem])
async def read_observaciones(
    skip: int = 0,
    limit: int = 100,
    filtro_id: Optional[int] = None,
    observatorio_id: Optional[int] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    objeto: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    """Get all observaciones with optional filters."""
    return await get_observaciones(
        db,
        skip=skip,
        limit=limit,
        filtro_id=filtro_id,
        observatorio_id=observatorio_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        objeto=objeto,
    )


@router.get("/{observacion_id}", response_model=ObservacionRead)
async def read_observacion(observacion_id: int, db: AsyncSession = Depends(get_session)):
    """Get a specific observacion by ID with all nested data."""
    obs = await get_observacion(db, observacion_id)
    if not obs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observacion not found")
    return obs


@router.post("", response_model=ObservacionRead, status_code=status.HTTP_201_CREATED)
async def create_observacion_endpoint(obj_in: ObservacionCreate, db: AsyncSession = Depends(get_session)):
    """Create a new observacion with nested sesiones and calibraciones."""
    return await create_observacion(db, obj_in)


@router.put("/{observacion_id}", response_model=ObservacionRead)
async def update_observacion_endpoint(
    observacion_id: int, obj_in: ObservacionUpdate, db: AsyncSession = Depends(get_session)
):
    """Update an observacion."""
    obs = await get_observacion(db, observacion_id)
    if not obs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observacion not found")
    return await update_observacion(db, obs, obj_in)


@router.post("/{observacion_id}/duplicate", response_model=ObservacionRead)
async def duplicate_observacion_endpoint(observacion_id: int, db: AsyncSession = Depends(get_session)):
    """Duplicate an observacion with all nested data."""
    try:
        return await duplicate_observacion(db, observacion_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observacion not found")


@router.delete("/{observacion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observacion_endpoint(observacion_id: int, db: AsyncSession = Depends(get_session)):
    """Delete an observacion."""
    success = await delete_observacion(db, observacion_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observacion not found")