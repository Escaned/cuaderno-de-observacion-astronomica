import pytest
import pytest_asyncio
import tempfile
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import inspect

from app.core.database import Base
from app.models import Observatorio, Filtro, Observacion, SesionCaptura, Calibracion


@pytest_asyncio.fixture(scope="function")
async def db_session():
    # Use temporary file for SQLite to avoid connection sharing issues
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=False,
            poolclass=NullPool,
            connect_args={"check_same_thread": False},
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session
            await session.rollback()
        
        await engine.dispose()
    finally:
        # Clean up temp file
        if os.path.exists(db_path):
            os.unlink(db_path)