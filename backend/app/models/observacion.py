from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class Observacion(Base):
    __tablename__ = "observaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    objeto = Column(String(100), nullable=False, index=True)
    fecha_hora_utc = Column(DateTime, nullable=False, index=True)
    filtro_id = Column(Integer, ForeignKey("filtros.id"), nullable=True)
    fwhm = Column(Float, nullable=False)
    temperatura = Column(Float, nullable=True)
    humedad = Column(Integer, nullable=True)
    viento_kph = Column(Float, nullable=True)
    direccion_viento = Column(String(10), nullable=True)
    descripcion = Column(Text, nullable=True)
    imagenes = Column(Text, nullable=True)  # JSON array as text
    creado_en = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    actualizado_en = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    filtro = relationship("Filtro", back_populates="observaciones")
    sesiones_captura = relationship("SesionCaptura", back_populates="observacion", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("fwhm >= 0.5 AND fwhm <= 10.0", name="ck_observacion_fwhm_range"),
        CheckConstraint("humedad IS NULL OR (humedad >= 0 AND humedad <= 100)", name="ck_observacion_humedad_range"),
        Index("ix_observaciones_fecha_objeto", "fecha_hora_utc", "objeto"),
    )

    def __repr__(self):
        return f"<Observacion(id={self.id}, objeto='{self.objeto}', fecha_utc='{self.fecha_hora_utc}')>"