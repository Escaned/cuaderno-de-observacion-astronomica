from pydantic import BaseModel, ConfigDict
from typing import Optional


class SesionCapturaBase(BaseModel):
    filtro_id: int
    tiempo_exposicion_seg: float
    num_subs: int
    binning: int = 1
    gain: Optional[int] = None
    offset: Optional[int] = None
    temp_sensor: Optional[float] = None


class SesionCapturaRead(SesionCapturaBase):
    id: int
    observacion_id: int
    calibraciones_count: int = 0

    model_config = ConfigDict(from_attributes=True)