from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, CheckConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TipoCalibracion(str, enum.Enum):
    dark = "dark"
    flat = "flat"
    bias = "bias"
    darkflat = "darkflat"


class Calibracion(Base):
    __tablename__ = "calibracion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sesion_captura_id = Column(Integer, ForeignKey("sesiones_captura.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(SQLEnum(TipoCalibracion), nullable=False)
    count = Column(Integer, nullable=False)
    tiempo_exposicion_seg = Column(Float, nullable=True)
    temperatura = Column(Float, nullable=True)
    filtro_id = Column(Integer, ForeignKey("filtros.id"), nullable=True)
    notas = Column(Text, nullable=True)

    # Relationships
    sesion_captura = relationship("SesionCaptura", back_populates="calibraciones")
    filtro = relationship("Filtro", back_populates="calibraciones_flats")

    __table_args__ = (
        CheckConstraint("count >= 0", name="ck_calibracion_count_nonneg"),
    )

    def __repr__(self):
        return f"<Calibracion(id={self.id}, tipo={self.tipo.value}, count={self.count})>"