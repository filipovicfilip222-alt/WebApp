"""
SQLAlchemy database setup with async support.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    connect_args={
        "command_timeout": 60,
        "timeout": 60,
    },
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db():
    """Dependency for getting database session in FastAPI routes."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
