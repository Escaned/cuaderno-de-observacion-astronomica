import sqlite3

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import init_db, get_session


@pytest.mark.asyncio
async def test_init_db_applies_every_migration(tmp_path):
    # A startup that only did create_all left old databases with the old columns,
    # and every observatory request failed with a 500. init_db has to migrate.
    database = tmp_path / "riguel.db"

    await init_db(f"sqlite+aiosqlite:///{database.as_posix()}")

    connection = sqlite3.connect(database)
    try:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        nombre = connection.execute("SELECT nombre FROM asociacion WHERE id = 1").fetchone()[0]
        sitios = connection.execute("SELECT COUNT(*) FROM observatorio").fetchone()[0]
        columnas = {row[1] for row in connection.execute("PRAGMA table_info(observatorio)")}
    finally:
        connection.close()

    assert revision == "0004"
    assert nombre == "Riguel"
    assert sitios == 1
    assert "color" in columnas
    assert "es_predeterminado" in columnas


@pytest.mark.asyncio
async def test_get_session_yields_session():
    async for session in get_session():
        assert isinstance(session, AsyncSession)
        break
