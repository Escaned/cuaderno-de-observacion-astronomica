from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class AsociacionBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    logo_path: Optional[str] = None


class AsociacionUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    logo_path: Optional[str] = None


class AsociacionRead(AsociacionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
