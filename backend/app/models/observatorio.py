from sqlalchemy import Column, Integer, String, Float, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Observatorio(Base):
    __tablename__ = "observatorio"

    id = Column(Integer, primary_key=True, nullable=False)
    nombre = Column(String(100), nullable=False, default="Riguel")
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    altitud_msnm = Column(Float, nullable=True)
    zona_horaria = Column(String(50), nullable=False, default="Europe/Madrid")

    __table_args__ = (
        CheckConstraint("id = 1", name="ck_observatorio_singleton"),
    )

    def __repr__(self):
        return f"<Observatorio(nombre='{self.nombre}', lat={self.latitud}, lon={self.longitud})>"