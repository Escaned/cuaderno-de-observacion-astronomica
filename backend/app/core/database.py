import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core import migrations
from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(database_url: str | None = None) -> None:
    """Bring the database up to date, applying every pending migration.

    `create_all` alone is not enough: it creates missing tables but never alters an
    existing one, so a database from an older version keeps its old columns and the
    new code fails against it with a 500 that looks like a bug in the screen. Run on
    startup so every way of starting the app - launcher, `arrancar.bat`, uvicorn -
    upgrades the database before serving requests.

    Alembic's environment script calls `asyncio.run()`, which cannot run inside the
    event loop FastAPI already owns; a worker thread gets its own loop.
    """
    await asyncio.to_thread(
        migrations.upgrade_to_head, database_url or settings.database_url
    )


async def close_db() -> None:
    await engine.dispose()