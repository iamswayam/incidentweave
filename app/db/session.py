"""SQLAlchemy engine and session management."""

from collections.abc import AsyncGenerator

from pgvector.psycopg import register_vector_async
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _async_database_url(database_url: str) -> str:
    """Convert the configured PostgreSQL URL to the psycopg async dialect."""

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


engine = create_async_engine(
    _async_database_url(settings.database_url),
    pool_pre_ping=True,
)


@event.listens_for(engine.sync_engine, "connect")
def _register_pgvector(dbapi_connection: object, connection_record: object) -> None:
    """Register pgvector types for each async psycopg connection."""

    del connection_record
    dbapi_connection.run_async(register_vector_async)  # type: ignore[attr-defined]


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an application database session."""

    async with AsyncSessionLocal() as session:
        yield session
