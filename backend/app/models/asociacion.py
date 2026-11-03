from sqlalchemy import Column, Integer, String, CheckConstraint

from app.core.database import Base


class Asociacion(Base):
    """Datos de la asociacion (fila unica, id=1).

    El nombre y el logo son de la asociacion, no de un observatorio concreto:
    una asociacion puede tener varios observatorios.
    """

    __tablename__ = "asociacion"

    id = Column(Integer, primary_key=True, nullable=False)
    nombre = Column(String(100), nullable=False, default="Riguel")
    logo_path = Column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint("id = 1", name="ck_asociacion_singleton"),
    )

    def __repr__(self):
        return f"<Asociacion(nombre='{self.nombre}')>"
