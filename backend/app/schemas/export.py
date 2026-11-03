from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum


class ExportFormat(str, Enum):
    csv = "csv"
    pdf = "pdf"


class CSVExportRequest(BaseModel):
    tabla: Literal["observaciones", "sesiones_captura", "calibracion", "filtros", "asociacion", "observatorios", "observatorio", "all"] = "all"
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    filtro_id: Optional[int] = None


class CSVExportResponse(BaseModel):
    filename: str
    content_type: str = "text/csv"
    size_bytes: int


class PDFExportRequest(BaseModel):
    tipo: Literal["noche", "campana"]
    fecha_desde: datetime
    fecha_hasta: datetime
    filtro_id: Optional[int] = None


class PDFExportResponse(BaseModel):
    filename: str
    content_type: str = "application/pdf"
    size_bytes: int


class ExportStatus(BaseModel):
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = 0
    download_url: Optional[str] = None
    error: Optional[str] = None