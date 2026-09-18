from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Task, TaskAssignment, TaskStatus
from app.routers.tasks import _to_out

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("")
async def dashboard(db: AsyncSession = Depends(get_db)):
    """Vue agrégée pour l'écran TV : tâches en cours + à faire, avec les personnes
    affiliées et le temps restant (calculé côté client depuis date_fin_prevue)."""
    query = (
        select(Task)
        .where(Task.statut.in_([TaskStatus.a_faire, TaskStatus.en_cours, TaskStatus.en_retard]))
        .options(selectinload(Task.assignments).selectinload(TaskAssignment.user))
        .order_by(Task.date_fin_prevue.asc().nulls_last())
    )
    result = await db.execute(query)
    tasks = result.scalars().unique().all()
    return {
        "en_cours": [_to_out(t) for t in tasks if t.statut == TaskStatus.en_cours],
        "a_faire": [_to_out(t) for t in tasks if t.statut == TaskStatus.a_faire],
        "en_retard": [_to_out(t) for t in tasks if t.statut == TaskStatus.en_retard],
    }
