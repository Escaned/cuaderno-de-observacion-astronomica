from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class CalibracionBase(BaseModel):
    tipo: str  # dark, flat, bias, darkflat
    count: int = Field(ge=0)
    tiempo_exposicion_seg: Optional[float] = None
    temperatura: Optional[float] = None
    filtro_id: Optional[int] = None
    notas: Optional[str] = None


class CalibracionCreate(CalibracionBase):
    pass


class CalibracionUpdate(BaseModel):
    tipo: Optional[str] = None
    count: Optional[int] = Field(default=None, ge=0)
    tiempo_exposicion_seg: Optional[float] = None
    temperatura: Optional[float] = None
    filtro_id: Optional[int] = None
    notas: Optional[str] = None


class CalibracionRead(CalibracionBase):
    id: int
    sesion_captura_id: int

    model_config = ConfigDict(from_attributes=True)