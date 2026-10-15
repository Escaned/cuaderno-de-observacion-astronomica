from datetime import datetime
from typing import Optional
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Observacion, SesionCaptura, Calibracion, Filtro, Observatorio


def _logo_flowable(logo_path: Optional[str], max_height_cm: float = 1.6):
    """Build a ReportLab Image flowable for the association logo.

    Returns None when there is no logo configured or the file is missing, so the
    PDF keeps working without it. The aspect ratio is preserved.
    """
    if not logo_path:
        return None

    from pathlib import Path

    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image

    from app.core.config import settings

    path = Path(settings.images_dir) / Path(logo_path).name
    if not path.is_file():
        return None

    try:
        width_px, height_px = ImageReader(str(path)).getSize()
    except Exception:
        return None

    if not width_px or not height_px:
        return None

    height = max_height_cm * cm
    return Image(str(path), width=height * (width_px / height_px), height=height)


def _header_table(logo, title_flowables):
    """Logo on the left, title block on the right. Works when there is no logo."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle

    header = Table([[logo or "", title_flowables]], colWidths=[2.6 * cm, 14.4 * cm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return header


async def generate_night_pdf(db: AsyncSession, fecha: datetime) -> bytes:
    """Generate a PDF report for a single night (all observations on that date)."""
    start_of_day = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)

    query = (
        select(Observacion)
        .options(
            selectinload(Observacion.filtro),
            selectinload(Observacion.sesiones_captura).selectinload(SesionCaptura.filtro),
            selectinload(Observacion.sesiones_captura).selectinload(SesionCaptura.calibraciones),
        )
        .where(Observacion.fecha_hora_utc >= start_of_day, Observacion.fecha_hora_utc <= end_of_day)
        .order_by(Observacion.fecha_hora_utc)
    )
    result = await db.execute(query)
    observaciones = list(result.scalars().unique().all())

    if not observaciones:
        raise ValueError("No observations found for this date")

    obs_result = await db.execute(select(Observatorio))
    observatorio = obs_result.scalar_one_or_none()

    return _generate_night_pdf_reportlab(observaciones, observatorio, fecha)


async def generate_campaign_pdf(db: AsyncSession, fecha_desde: datetime, fecha_hasta: datetime) -> bytes:
    """Generate a PDF report for a campaign (date range)."""
    query = (
        select(Observacion)
        .options(
            selectinload(Observacion.filtro),
            selectinload(Observacion.sesiones_captura).selectinload(SesionCaptura.filtro),
            selectinload(Observacion.sesiones_captura).selectinload(SesionCaptura.calibraciones),
        )
        .where(Observacion.fecha_hora_utc >= fecha_desde, Observacion.fecha_hora_utc <= fecha_hasta)
        .order_by(Observacion.fecha_hora_utc)
    )
    result = await db.execute(query)
    observaciones = list(result.scalars().unique().all())

    if not observaciones:
        raise ValueError("No observations found for this date range")

    obs_result = await db.execute(select(Observatorio))
    observatorio = obs_result.scalar_one_or_none()

    return _generate_campaign_pdf_reportlab(observaciones, observatorio, fecha_desde, fecha_hasta)


def _generate_night_pdf_reportlab(observaciones, observatorio, fecha) -> bytes:
    """Generate night PDF using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    obs_name = observatorio.nombre if observatorio else "Observatorio"
    obs_location = f"{observatorio.latitud:.4f}, {observatorio.longitud:.4f}" if observatorio else ""

    elements.append(_header_table(
        _logo_flowable(observatorio.logo_path if observatorio else None),
        [
            Paragraph(f"<b>Informe de Noche - {obs_name}</b>", styles["Title"]),
            Paragraph(f"Fecha: {fecha.strftime('%d/%m/%Y')} | Ubicacion: {obs_location}", styles["Normal"]),
        ],
    ))
    elements.append(Spacer(1, 0.5*cm))

    total_sesiones = sum(len(obs.sesiones_captura) for obs in observaciones)
    total_calibraciones = sum(len(sesion.calibraciones) for obs in observaciones for sesion in obs.sesiones_captura)
    total_exposure = sum(sesion.total_tiempo_seg for obs in observaciones for sesion in obs.sesiones_captura)

    elements.append(Paragraph("<b>Resumen</b>", styles["Heading2"]))
    summary_data = [
        ["Observaciones", str(len(observaciones))],
        ["Sesiones de captura", str(total_sesiones)],
        ["Calibraciones", str(total_calibraciones)],
        ["Tiempo total exposicion", f"{total_exposure/3600:.2f}h"],
    ]
    summary_table = Table(summary_data, colWidths=[6*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("<b>Detalle</b>", styles["Heading2"]))
    for obs in observaciones:
        filtro_nombre = obs.filtro.nombre if obs.filtro else "-"
        elements.append(Paragraph(f"<b>{obs.objeto}</b> - {obs.fecha_hora_utc.strftime('%H:%M')} UTC | FWHM: {obs.fwhm:.1f}\" | Filtro: {filtro_nombre}", styles["Normal"]))

        for sesion in obs.sesiones_captura:
            sesion_filtro = sesion.filtro.nombre if sesion.filtro else "-"
            elements.append(Paragraph(f"  Filtro: {sesion_filtro} | {sesion.tiempo_exposicion_seg}s x {sesion.num_subs} | Binning: {sesion.binning} | Temp: {sesion.temp_sensor or '-'} C", styles["Normal"]))

    doc.build(elements)
    return buffer.getvalue()


def _generate_campaign_pdf_reportlab(observaciones, observatorio, fecha_desde, fecha_hasta) -> bytes:
    """Generate campaign PDF using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    obs_name = observatorio.nombre if observatorio else "Observatorio"

    elements.append(_header_table(
        _logo_flowable(observatorio.logo_path if observatorio else None),
        [
            Paragraph(f"<b>Informe de Campana - {obs_name}</b>", styles["Title"]),
            Paragraph(f"Periodo: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}", styles["Normal"]),
        ],
    ))
    elements.append(Spacer(1, 0.5*cm))

    objetos = {}
    for obs in observaciones:
        if obs.objeto not in objetos:
            objetos[obs.objeto] = []
        objetos[obs.objeto].append(obs)

    total_exposure = sum(sesion.total_tiempo_seg for obs in observaciones for sesion in obs.sesiones_captura)

    elements.append(Paragraph("<b>Resumen</b>", styles["Heading2"]))
    summary_data = [
        ["Objetos observados", str(len(objetos))],
        ["Noches de observacion", str(len(set(obs.fecha_hora_utc.date() for obs in observaciones)))],
        ["Total observaciones", str(len(observaciones))],
        ["Tiempo total exposicion", f"{total_exposure/3600:.2f}h"],
    ]
    summary_table = Table(summary_data, colWidths=[6*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("<b>Por Objeto</b>", styles["Heading2"]))
    obj_data = [["Objeto", "Noches", "Tiempo exposicion", "FWHM medio"]]
    for obj_name, obs_list in objetos.items():
        total_obj = sum(sesion.total_tiempo_seg for obs in obs_list for sesion in obs.sesiones_captura)
        fwhm_medio = sum(obs.fwhm for obs in obs_list) / len(obs_list)
        obj_data.append([obj_name, str(len(obs_list)), f"{total_obj/3600:.2f}h", f"{fwhm_medio:.1f}\""])

    obj_table = Table(obj_data, colWidths=[4.5*cm, 2.5*cm, 3.5*cm, 3.5*cm])
    obj_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(obj_table)

    doc.build(elements)
    return buffer.getvalue()