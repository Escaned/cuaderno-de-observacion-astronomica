from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Observatorio
from app.schemas import ObservatorioCreate, ObservatorioUpdate

# Colors offered when the user does not pick one. They are easy to tell apart
# and stay readable on both the light and the dark theme.
PALETA_COLORES = (
    "#4d48e2",  # indigo (el color historico de la app)
    "#0f766e",  # verde azulado
    "#b45309",  # ambar
    "#be123c",  # carmin
    "#7e22ce",  # purpura
    "#0369a1",  # azul
    "#4d7c0f",  # oliva
    "#9f1239",  # vino
)


def _color_por_orden(orden: int) -> str:
    return PALETA_COLORES[orden % len(PALETA_COLORES)]


async def get_observatorio(db: AsyncSession, observatorio_id: int) -> Observatorio | None:
    result = await db.execute(select(Observatorio).where(Observatorio.id == observatorio_id))
    return result.scalar_one_or_none()


async def get_observatorios(db: AsyncSession) -> list[Observatorio]:
    """All observatories, the default one first, then by name."""
    result = await db.execute(
        select(Observatorio).order_by(
            Observatorio.es_predeterminado.desc(),
            Observatorio.nombre.asc(),
            Observatorio.id.asc(),
        )
    )
    return list(result.scalars().all())


async def count_observatorios(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(Observatorio.id)))
    return int(result.scalar_one())


async def get_predeterminado(db: AsyncSession) -> Observatorio | None:
    """The default observatory, falling back to the first one that exists."""
    result = await db.execute(
        select(Observatorio)
        .where(Observatorio.es_predeterminado.is_(True))
        .order_by(Observatorio.id.asc())
        .limit(1)
    )
    predeterminado = result.scalar_one_or_none()
    if predeterminado:
        return predeterminado

    result = await db.execute(select(Observatorio).order_by(Observatorio.id.asc()).limit(1))
    return result.scalar_one_or_none()


async def get_or_create_predeterminado(db: AsyncSession) -> Observatorio:
    """The default observatory, creating the seed one when the table is empty."""
    observatorio = await get_predeterminado(db)
    if observatorio:
        return observatorio

    from app.core.config import settings

    return await create_observatorio(
        db,
        ObservatorioCreate(
            nombre=settings.obs_nombre,
            latitud=settings.obs_lat,
            longitud=settings.obs_lon,
            altitud_msnm=settings.obs_alt,
            zona_horaria=settings.obs_tz,
            es_predeterminado=True,
        ),
    )


async def _clear_predeterminado(db: AsyncSession, excepto_id: int | None = None) -> None:
    query = update(Observatorio).values(es_predeterminado=False)
    if excepto_id is not None:
        query = query.where(Observatorio.id != excepto_id)
    await db.execute(query)


async def set_predeterminado(db: AsyncSession, observatorio_id: int) -> Observatorio | None:
    """Make one observatory the default, unmarking every other one."""
    observatorio = await get_observatorio(db, observatorio_id)
    if not observatorio:
        return None

    await _clear_predeterminado(db, excepto_id=observatorio_id)
    observatorio.es_predeterminado = True
    db.add(observatorio)
    await db.commit()
    await db.refresh(observatorio)
    return observatorio


async def create_observatorio(db: AsyncSession, obj_in: ObservatorioCreate) -> Observatorio:
    total = await count_observatorios(db)

    data = obj_in.model_dump()
    # The first observatory is always the default: without one, the
    # observations screen has nothing preselected.
    if total == 0:
        data["es_predeterminado"] = True
    if not data.get("color"):
        data["color"] = _color_por_orden(total)

    if data["es_predeterminado"]:
        await _clear_predeterminado(db)

    db_obj = Observatorio(**data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_observatorio(
    db: AsyncSession, db_obj: Observatorio, obj_in: ObservatorioUpdate
) -> Observatorio:
    update_data = obj_in.model_dump(exclude_unset=True)

    # There must always be exactly one default. Changing it goes through
    # set_predeterminado(); here we only accept turning another one on and
    # ignore an attempt to leave the default one off.
    if update_data.get("es_predeterminado") is True:
        await _clear_predeterminado(db, excepto_id=db_obj.id)
    elif update_data.get("es_predeterminado") is False and db_obj.es_predeterminado:
        update_data.pop("es_predeterminado", None)

    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_observatorio(db: AsyncSession, db_obj: Observatorio) -> None:
    from app.models import Observacion

    era_predeterminado = db_obj.es_predeterminado

    # SQLite no aplica ON DELETE SET NULL salvo que se active el PRAGMA, asi que
    # las observaciones se desvinculan a mano: no se borran, dejan de tener sitio.
    await db.execute(
        update(Observacion)
        .where(Observacion.observatorio_id == db_obj.id)
        .values(observatorio_id=None)
    )
    await db.delete(db_obj)
    await db.flush()

    if era_predeterminado:
        # The screen needs a default, so promote whichever one is left.
        result = await db.execute(select(Observatorio).order_by(Observatorio.id.asc()).limit(1))
        siguiente = result.scalar_one_or_none()
        if siguiente:
            siguiente.es_predeterminado = True
            db.add(siguiente)

    await db.commit()
