import pytest
from datetime import datetime, timezone
from sqlalchemy import select

from app.models import Observatorio, Filtro, Observacion, SesionCaptura, Calibracion, TipoCalibracion


@pytest.mark.asyncio
async def test_observatorio_singleton(db_session):
    obs = Observatorio(nombre="Test", latitud=1.0, longitud=2.0, altitud_msnm=100.0)
    db_session.add(obs)
    await db_session.commit()

    result = await db_session.execute(select(Observatorio))
    observatorios = result.scalars().all()
    assert len(observatorios) == 1
    assert observatorios[0].nombre == "Test"
    assert observatorios[0].id == 1


@pytest.mark.asyncio
async def test_filtro_crud(db_session):
    filtro = Filtro(nombre="TestFilter", descripcion="Test", onda_central_nm=500.0, orden=1, activo=True)
    db_session.add(filtro)
    await db_session.commit()
    await db_session.refresh(filtro)

    assert filtro.id is not None
    assert filtro.nombre == "TestFilter"
    assert filtro.activo is True


@pytest.mark.asyncio
async def test_filtro_unique_nombre(db_session):
    f1 = Filtro(nombre="Unique", orden=1)
    f2 = Filtro(nombre="Unique", orden=2)
    db_session.add_all([f1, f2])
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_observacion_with_seeing_constraint(db_session):
    obs = Observacion(
        objeto="M42",
        fecha_hora_utc=datetime.now(timezone.utc),
        seeing=3,
        temperatura=15.0,
    )
    db_session.add(obs)
    await db_session.commit()

    result = await db_session.execute(select(Observacion).where(Observacion.objeto == "M42"))
    saved = result.scalar_one()
    assert saved.seeing == 3


@pytest.mark.asyncio
async def test_observacion_seeing_out_of_range_fails(db_session):
    obs = Observacion(
        objeto="M42",
        fecha_hora_utc=datetime.now(timezone.utc),
        seeing=10,  # Invalid: must be 1-5
    )
    db_session.add(obs)
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_sesion_captura_relationship(db_session):
    filtro = Filtro(nombre="Ha", orden=1, activo=True)
    db_session.add(filtro)
    await db_session.flush()

    obs = Observacion(objeto="M42", fecha_hora_utc=datetime.now(timezone.utc), seeing=3)
    db_session.add(obs)
    await db_session.flush()

    sesion = SesionCaptura(
        observacion_id=obs.id,
        filtro_id=filtro.id,
        tiempo_exposicion_seg=300.0,
        num_subs=20,
        binning=1,
        gain=100,
        temp_sensor=-10.0,
    )
    db_session.add(sesion)
    await db_session.commit()
    await db_session.refresh(sesion)

    assert sesion.total_tiempo_seg == 6000.0  # 300 * 20
    assert sesion.observacion_id == obs.id
    assert sesion.filtro_id == filtro.id


@pytest.mark.asyncio
async def test_calibracion_types(db_session):
    filtro = Filtro(nombre="Ha", orden=1, activo=True)
    db_session.add(filtro)
    await db_session.flush()

    obs = Observacion(objeto="M42", fecha_hora_utc=datetime.now(timezone.utc), seeing=3)
    db_session.add(obs)
    await db_session.flush()

    sesion = SesionCaptura(observacion_id=obs.id, filtro_id=filtro.id, tiempo_exposicion_seg=300, num_subs=10)
    db_session.add(sesion)
    await db_session.flush()

    for tipo in TipoCalibracion:
        cal = Calibracion(
            sesion_captura_id=sesion.id,
            tipo=tipo,
            count=10 if tipo != TipoCalibracion.bias else 50,
            tiempo_exposicion_seg=300.0 if tipo in (TipoCalibracion.dark, TipoCalibracion.flat) else None,
            temperatura=-10.0 if tipo == TipoCalibracion.dark else None,
            filtro_id=filtro.id if tipo == TipoCalibracion.flat else None,
        )
        db_session.add(cal)

    await db_session.commit()

    result = await db_session.execute(select(Calibracion).where(Calibracion.sesion_captura_id == sesion.id))
    cals = result.scalars().all()
    assert len(cals) == 4


@pytest.mark.asyncio
async def test_cascade_delete_observacion_removes_sesiones(db_session):
    filtro = Filtro(nombre="Ha", orden=1, activo=True)
    db_session.add(filtro)
    await db_session.flush()

    obs = Observacion(objeto="M42", fecha_hora_utc=datetime.now(timezone.utc), seeing=3)
    db_session.add(obs)
    await db_session.flush()

    sesion = SesionCaptura(observacion_id=obs.id, filtro_id=filtro.id, tiempo_exposicion_seg=300, num_subs=10)
    db_session.add(sesion)
    await db_session.commit()

    await db_session.delete(obs)
    await db_session.commit()

    result = await db_session.execute(select(SesionCaptura).where(SesionCaptura.observacion_id == obs.id))
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_cascade_delete_sesion_removes_calibracion(db_session):
    filtro = Filtro(nombre="Ha", orden=1, activo=True)
    db_session.add(filtro)
    await db_session.flush()

    obs = Observacion(objeto="M42", fecha_hora_utc=datetime.now(timezone.utc), seeing=3)
    db_session.add(obs)
    await db_session.flush()

    sesion = SesionCaptura(observacion_id=obs.id, filtro_id=filtro.id, tiempo_exposicion_seg=300, num_subs=10)
    db_session.add(sesion)
    await db_session.flush()

    cal = Calibracion(sesion_captura_id=sesion.id, tipo=TipoCalibracion.dark, count=10, tiempo_exposicion_seg=300, temperatura=-10)
    db_session.add(cal)
    await db_session.commit()

    await db_session.delete(sesion)
    await db_session.commit()

    result = await db_session.execute(select(Calibracion).where(Calibracion.sesion_captura_id == sesion.id))
    assert result.scalars().all() == []