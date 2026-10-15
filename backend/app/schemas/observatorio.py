from pydantic import BaseModel, ConfigDict
from typing import Optional


class ObservatorioBase(BaseModel):
    nombre: str
    latitud: float
    longitud: float
    altitud_msnm: Optional[float] = None
    zona_horaria: str = "Europe/Madrid"
    logo_path: Optional[str] = None


class ObservatorioCreate(ObservatorioBase):
    pass


class ObservatorioUpdate(BaseModel):
    nombre: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    altitud_msnm: Optional[float] = None
    zona_horaria: Optional[str] = None
    logo_path: Optional[str] = None


class ObservatorioRead(ObservatorioBase):
    id: int

    model_config = ConfigDict(from_attributes=True)