from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.core.database import get_session
from app.services.csv_generator import generate_csv_export
from app.services.pdf_generator import generate_night_pdf, generate_campaign_pdf

router = APIRouter()


@router.get("/csv")
async def export_csv(
    tabla: str = Query("all", description="Table to export: observaciones, sesiones_captura, calibracion, filtros, asociacion, observatorios, or all"),
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    filtro_id: Optional[int] = None,
    db: AsyncSession = Depends(get_session),
):
    """Export data as CSV. When tabla='all', combines all tables into a single CSV with section headers."""
    if tabla not in (
        "observaciones", "sesiones_captura", "calibracion", "filtros",
        "asociacion", "observatorios", "observatorio", "all",
    ):
        raise HTTPException(status_code=400, detail="Invalid table name")

    content = await generate_csv_export(db, tabla, fecha_desde, fecha_hasta, filtro_id)

    filename = f"export_{tabla}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    content_type = "text/csv"

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/pdf/noche")
async def export_pdf_noche(
    fecha: datetime = Query(..., description="Date of the night to export (ISO format)"),
    db: AsyncSession = Depends(get_session),
):
    """Export a single night report as PDF."""
    try:
        pdf_bytes = await generate_night_pdf(db, fecha)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    filename = f"informe_noche_{fecha.strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/pdf/campana")
async def export_pdf_campana(
    fecha_desde: datetime = Query(..., description="Start date (ISO format)"),
    fecha_hasta: datetime = Query(..., description="End date (ISO format)"),
    db: AsyncSession = Depends(get_session),
):
    """Export a campaign report as PDF."""
    try:
        pdf_bytes = await generate_campaign_pdf(db, fecha_desde, fecha_hasta)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    filename = f"informe_campana_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )