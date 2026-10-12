from sqlalchemy import Column, Integer, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class SesionCaptura(Base):
    __tablename__ = "sesiones_captura"

    id = Column(Integer, primary_key=True, autoincrement=True)
    observacion_id = Column(Integer, ForeignKey("observaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    filtro_id = Column(Integer, ForeignKey("filtros.id"), nullable=False)
    tiempo_exposicion_seg = Column(Float, nullable=False)
    num_subs = Column(Integer, nullable=False)
    binning = Column(Integer, nullable=False, default=1)
    temp_sensor = Column(Float, nullable=True)

    # Relationships
    observacion = relationship("Observacion", back_populates="sesiones_captura")
    filtro = relationship("Filtro", back_populates="sesiones_captura")
    calibraciones = relationship("Calibracion", back_populates="sesion_captura", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("tiempo_exposicion_seg > 0", name="ck_sesion_exposicion_positive"),
        CheckConstraint("num_subs > 0", name="ck_sesion_subs_positive"),
        CheckConstraint("binning >= 1", name="ck_sesion_binning_positive"),
    )

    @property
    def total_tiempo_seg(self) -> float:
        return self.tiempo_exposicion_seg * self.num_subs

    def __repr__(self):
        return f"<SesionCaptura(id={self.id}, filtro_id={self.filtro_id}, {self.tiempo_exposicion_seg}s x {self.num_subs})>"