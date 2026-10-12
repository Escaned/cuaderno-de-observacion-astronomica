import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import init_db, close_db, get_session


@pytest.mark.asyncio
async def test_init_db_creates_tables():
    await init_db()
    await close_db()
    # If we get here without exception, tables were created


@pytest.mark.asyncio
async def test_get_session_yields_session():
    async for session in get_session():
        assert isinstance(session, AsyncSession)
        break