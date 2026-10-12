from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.crud import (
    get_observatorio,
    create_observatorio,
    update_observatorio,
    get_or_create_observatorio,
)
from app.schemas import ObservatorioCreate, ObservatorioUpdate, ObservatorioRead

router = APIRouter()


@router.get("", response_model=ObservatorioRead)
async def read_observatorio(db: AsyncSession = Depends(get_session)):
    """Get observatorio configuration."""
    obs = await get_or_create_observatorio(db)
    return obs


@router.put("", response_model=ObservatorioRead)
async def update_observatorio_endpoint(
    obj_in: ObservatorioUpdate, db: AsyncSession = Depends(get_session)
):
    """Update observatorio configuration."""
    obs = await get_or_create_observatorio(db)
    return await update_observatorio(db, obs, obj_in)