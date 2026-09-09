from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Créé les tables si elles n'existent pas encore (dev only — utiliser Alembic en prod)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Rustine dev pour les colonnes ajoutées après le premier déploiement
        # (à remplacer par une vraie migration Alembic en prod).
        from sqlalchemy import text

        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_url VARCHAR(255)"))
