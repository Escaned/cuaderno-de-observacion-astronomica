from sqlalchemy import Column, Integer, String, Float, Boolean, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Filtro(Base):
    __tablename__ = "filtros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(20), nullable=False, unique=True)
    descripcion = Column(String(200), nullable=True)
    onda_central_nm = Column(Float, nullable=True)
    orden = Column(Integer, nullable=False, default=0)
    activo = Column(Boolean, nullable=False, default=True)

    # Relationships
    observaciones = relationship("Observacion", back_populates="filtro")
    sesiones_captura = relationship("SesionCaptura", back_populates="filtro")
    calibraciones_flats = relationship("Calibracion", back_populates="filtro")

    def __repr__(self):
        return f"<Filtro(nombre='{self.nombre}', orden={self.orden}, activo={self.activo})>"