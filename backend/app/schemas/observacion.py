from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List


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


class SesionCapturaBase(BaseModel):
    filtro_id: int
    tiempo_exposicion_seg: float = Field(gt=0)
    num_subs: int = Field(gt=0)
    binning: int = Field(default=1, ge=1, le=2)
    temp_sensor: Optional[float] = None


class SesionCapturaCreate(SesionCapturaBase):
    calibraciones: List[CalibracionCreate] = []


class SesionCapturaUpdate(BaseModel):
    filtro_id: Optional[int] = None
    tiempo_exposicion_seg: Optional[float] = Field(default=None, gt=0)
    num_subs: Optional[int] = Field(default=None, gt=0)
    binning: Optional[int] = Field(default=None, ge=1, le=2)
    temp_sensor: Optional[float] = None
    calibraciones: Optional[List[CalibracionCreate]] = None


class SesionCapturaRead(SesionCapturaBase):
    id: int
    observacion_id: int
    calibraciones: List[CalibracionRead] = []

    model_config = ConfigDict(from_attributes=True)


class ObservacionBase(BaseModel):
    objeto: str
    fecha_hora_utc: datetime
    filtro_id: Optional[int] = None
    fwhm: float = Field(ge=0.5, le=10.0)
    temperatura: Optional[float] = None
    humedad: Optional[int] = Field(default=None, ge=0, le=100)
    viento_kph: Optional[float] = None
    direccion_viento: Optional[str] = Field(default=None, max_length=10)
    descripcion: Optional[str] = None
    imagenes: Optional[str] = None  # JSON array as text


class ObservacionCreate(ObservacionBase):
    sesiones_captura: List[SesionCapturaCreate] = []


class ObservacionUpdate(BaseModel):
    objeto: Optional[str] = None
    fecha_hora_utc: Optional[datetime] = None
    filtro_id: Optional[int] = None
    fwhm: Optional[float] = Field(default=None, ge=0.5, le=10.0)
    temperatura: Optional[float] = None
    humedad: Optional[int] = Field(default=None, ge=0, le=100)
    viento_kph: Optional[float] = None
    direccion_viento: Optional[str] = Field(default=None, max_length=10)
    descripcion: Optional[str] = None
    imagenes: Optional[str] = None
    sesiones_captura: Optional[List[SesionCapturaCreate]] = None


class ObservacionRead(ObservacionBase):
    id: int
    creado_en: datetime
    actualizado_en: datetime
    sesiones_captura: List[SesionCapturaRead] = []

    model_config = ConfigDict(from_attributes=True)


class ObservacionListItem(BaseModel):
    id: int
    objeto: str
    fecha_hora_utc: datetime
    filtro_id: Optional[int] = None
    fwhm: float
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)