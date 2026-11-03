from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.crud import (
    count_observatorios,
    create_observatorio,
    delete_observatorio,
    get_observatorio,
    get_observatorios,
    set_predeterminado,
    update_observatorio,
)
from app.schemas import ObservatorioCreate, ObservatorioRead, ObservatorioUpdate

router = APIRouter()


@router.get("", response_model=list[ObservatorioRead])
async def read_observatorios(db: AsyncSession = Depends(get_session)):
    """All observatories, the default one first."""
    return await get_observatorios(db)


@router.get("/{observatorio_id}", response_model=ObservatorioRead)
async def read_observatorio(observatorio_id: int, db: AsyncSession = Depends(get_session)):
    observatorio = await get_observatorio(db, observatorio_id)
    if not observatorio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observatorio no encontrado")
    return observatorio


@router.post("", response_model=ObservatorioRead, status_code=status.HTTP_201_CREATED)
async def create_observatorio_endpoint(
    obj_in: ObservatorioCreate, db: AsyncSession = Depends(get_session)
):
    """Create an observatory. The first one becomes the default."""
    return await create_observatorio(db, obj_in)


@router.put("/{observatorio_id}", response_model=ObservatorioRead)
async def update_observatorio_endpoint(
    observatorio_id: int,
    obj_in: ObservatorioUpdate,
    db: AsyncSession = Depends(get_session),
):
    observatorio = await get_observatorio(db, observatorio_id)
    if not observatorio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observatorio no encontrado")
    return await update_observatorio(db, observatorio, obj_in)


@router.post("/{observatorio_id}/predeterminado", response_model=ObservatorioRead)
async def set_predeterminado_endpoint(
    observatorio_id: int, db: AsyncSession = Depends(get_session)
):
    """Make this observatory the one selected by default."""
    observatorio = await set_predeterminado(db, observatorio_id)
    if not observatorio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observatorio no encontrado")
    return observatorio


@router.delete("/{observatorio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observatorio_endpoint(
    observatorio_id: int, db: AsyncSession = Depends(get_session)
):
    """Delete an observatory. The last one cannot be deleted."""
    observatorio = await get_observatorio(db, observatorio_id)
    if not observatorio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observatorio no encontrado")

    if await count_observatorios(db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Necesitás al menos un observatorio.",
        )

    await delete_observatorio(db, observatorio)
