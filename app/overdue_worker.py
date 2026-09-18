import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import Task, TaskAssignment, TaskStatus
from app.websocket_manager import manager

logger = logging.getLogger("taskboard.overdue")

CHECK_INTERVAL_SECONDS = 15


async def overdue_watch_loop() -> None:
    """Boucle de fond : détecte les tâches en_cours dont l'échéance est dépassée,
    les passe en en_retard et diffuse l'événement task.overdue (voir docs/CONCEPTION.md §4)."""
    while True:
        try:
            await _mark_overdue_tasks()
        except Exception:
            logger.exception("Erreur pendant la vérification des tâches en retard")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def _mark_overdue_tasks() -> None:
    from app.routers.tasks import _to_out  # import tardif pour éviter le cycle d'imports

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task).where(
                Task.statut == TaskStatus.en_cours,
                Task.date_fin_prevue < datetime.now(timezone.utc),
            )
        )
        overdue_tasks = result.scalars().all()
        if not overdue_tasks:
            return

        task_ids = [t.id for t in overdue_tasks]
        for task in overdue_tasks:
            task.statut = TaskStatus.en_retard
        await db.commit()

        refreshed = await db.execute(
            select(Task)
            .where(Task.id.in_(task_ids))
            .options(selectinload(Task.assignments).selectinload(TaskAssignment.user))
        )
        for task in refreshed.scalars().unique().all():
            logger.info("Tâche '%s' passée en retard", task.titre)
            await manager.broadcast({"type": "task.overdue", "task": _to_out(task).model_dump(mode="json")})
