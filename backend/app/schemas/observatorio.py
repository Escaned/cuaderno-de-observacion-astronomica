from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"


class ObservatorioBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)
    altitud_msnm: Optional[float] = Field(default=None, ge=-500, le=9000)
    zona_horaria: str = "Europe/Madrid"
    es_predeterminado: bool = False


class ObservatorioCreate(ObservatorioBase):
    color: Optional[str] = Field(default=None, pattern=COLOR_PATTERN)


class ObservatorioUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    latitud: Optional[float] = Field(default=None, ge=-90, le=90)
    longitud: Optional[float] = Field(default=None, ge=-180, le=180)
    altitud_msnm: Optional[float] = Field(default=None, ge=-500, le=9000)
    zona_horaria: Optional[str] = None
    color: Optional[str] = Field(default=None, pattern=COLOR_PATTERN)
    es_predeterminado: Optional[bool] = None


class ObservatorioRead(ObservatorioBase):
    id: int
    color: str

    model_config = ConfigDict(from_attributes=True)
