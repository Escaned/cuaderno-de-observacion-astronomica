from pydantic import BaseModel, ConfigDict
from typing import Optional


class FiltroBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    onda_central_nm: Optional[float] = None
    orden: int = 0
    activo: bool = True


class FiltroCreate(FiltroBase):
    pass


class FiltroUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    onda_central_nm: Optional[float] = None
    orden: Optional[int] = None
    activo: Optional[bool] = None


class FiltroReorder(BaseModel):
    filtro_id: int
    orden: int


class FiltroRead(FiltroBase):
    id: int

    model_config = ConfigDict(from_attributes=True)