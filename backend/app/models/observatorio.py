from sqlalchemy import Boolean, Column, Integer, String, Float, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Observatorio(Base):
    """Observatorio astronomico de la asociacion.

    Una asociacion puede tener varios observatorios. Solo uno es el
    predeterminado (el que se selecciona al abrir la pantalla de observaciones).
    """

    __tablename__ = "observatorio"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    nombre = Column(String(100), nullable=False, default="Riguel")
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    altitud_msnm = Column(Float, nullable=True)
    zona_horaria = Column(String(50), nullable=False, default="Europe/Madrid")
    color = Column(String(7), nullable=False, default="#4d48e2")
    es_predeterminado = Column(Boolean, nullable=False, default=False)

    observaciones = relationship("Observacion", back_populates="observatorio")

    __table_args__ = (
        CheckConstraint("latitud >= -90 AND latitud <= 90", name="ck_observatorio_latitud_range"),
        CheckConstraint("longitud >= -180 AND longitud <= 180", name="ck_observatorio_longitud_range"),
    )

    def __repr__(self):
        return f"<Observatorio(nombre='{self.nombre}', lat={self.latitud}, lon={self.longitud})>"
