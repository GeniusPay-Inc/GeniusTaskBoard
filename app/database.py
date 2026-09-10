import shutil
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Créer automatiquement le dossier parent si la base SQLite locale est utilisée
_sqlite_db_path: Path | None = None
if "sqlite" in settings.database_url:
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    if db_path and not db_path.startswith(":memory:"):
        _sqlite_db_path = Path(db_path)
        _sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite n'applique les contraintes FK (dont ON DELETE CASCADE) que si on
    l'active explicitement sur chaque connexion — ce n'est pas persistant."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


BACKUPS_TO_KEEP = 5


def _backup_sqlite_db() -> None:
    """Filet de sécurité avant toute migration : snapshot horodaté de la base
    (utile en cas d'erreur de migration ou de fausse manœuvre côté serveur —
    ne protège pas contre la suppression du volume Docker lui-même)."""
    if not _sqlite_db_path or not _sqlite_db_path.exists():
        return
    backups_dir = _sqlite_db_path.parent / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    shutil.copy2(_sqlite_db_path, backups_dir / f"{_sqlite_db_path.stem}_{stamp}.db")

    backups = sorted(backups_dir.glob(f"{_sqlite_db_path.stem}_*.db"))
    for stale in backups[:-BACKUPS_TO_KEEP]:
        stale.unlink(missing_ok=True)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Crée les tables au démarrage si elles n'existent pas encore."""
    _backup_sqlite_db()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Rustine dev pour les colonnes ajoutées après le premier déploiement
    # (à remplacer par une vraie migration Alembic en prod).
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN points INTEGER NOT NULL DEFAULT 0"))
        except OperationalError:
            pass  # colonne déjà présente
