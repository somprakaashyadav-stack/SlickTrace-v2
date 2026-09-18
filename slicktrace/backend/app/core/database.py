"""
SlickTrace v2 — Async SQLAlchemy database setup with PostGIS / SQLite fallback.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from loguru import logger
from app.core.config import settings

db_url = settings.DATABASE_URL
is_sqlite = "sqlite" in db_url
engine_kwargs = {"echo": False}
if not is_sqlite:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
    })

try:
    engine = create_async_engine(
        db_url,
        **engine_kwargs,
    )
except Exception as e:
    logger.warning(f"[DATABASE] Primary engine failed ({e}). Falling back to local SQLite.")
    db_url = "sqlite+aiosqlite:///slicktrace.db"
    engine = create_async_engine(db_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    global engine, AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except Exception as exc:
        # If postgres connection is refused, transparently fall back to local sqlite session
        if "postgresql" in settings.DATABASE_URL and "sqlite" not in str(engine.url):
            logger.warning(f"[DATABASE] PostgreSQL connection failed ({exc}). Switching to local SQLite schema.")
            engine = create_async_engine("sqlite+aiosqlite:///slicktrace.db", echo=False)
            AsyncSessionLocal = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            # Create tables in sqlite
            import app.models  # noqa
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async with AsyncSessionLocal() as session:
                yield session
                await session.commit()
        else:
            raise
