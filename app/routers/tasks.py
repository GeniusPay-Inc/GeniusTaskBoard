import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Task, TaskAssignment, TaskStatus, User
from app.schemas import TaskAssign, TaskCreate, TaskOut, TaskUpdate
from app.security import require_api_key
from app.websocket_manager import manager

router = APIRouter(prefix="/api/v1/tasks", tags=["tâches"])

POINTS_PER_ON_TIME_TASK = 10


async def _get_task_with_users(db: AsyncSession, task_id: uuid.UUID) -> Task:
    query = (
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.assignments).selectinload(TaskAssignment.user))
    )
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Tâche introuvable")
    return task


def _as_utc(dt: datetime) -> datetime:
    """SQLite ne conserve pas le fuseau horaire des DateTime(timezone=True) une
    fois relus depuis la base : on retombe sur un datetime naïf. On le
    réinterprète comme UTC (ce qu'il est toujours ici) pour pouvoir comparer
    en toute sécurité avec un datetime fraîchement créé, lui, tz-aware."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _to_out(task: Task) -> TaskOut:
    out = TaskOut.model_validate(task)
    out.assigned_users = [a.user for a in task.assignments]
    return out


async def _broadcast(event_type: str, task: Task) -> None:
    await manager.broadcast({"type": event_type, "task": _to_out(task).model_dump(mode="json")})


@router.post("", response_model=TaskOut, status_code=201, dependencies=[Depends(require_api_key)])
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump(exclude={"user_ids"})
    task = Task(**data)
    db.add(task)
    await db.flush()

    for user_id in payload.user_ids:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(404, f"Utilisateur {user_id} introuvable")
        db.add(TaskAssignment(task_id=task.id, user_id=user_id))

    await db.commit()
    task = await _get_task_with_users(db, task.id)
    await _broadcast("task.created", task)
    return _to_out(task)


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    statut: TaskStatus | None = None,
    user_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Task).options(selectinload(Task.assignments).selectinload(TaskAssignment.user))
    if statut:
        query = query.where(Task.statut == statut)
    if user_id:
        query = query.join(TaskAssignment).where(TaskAssignment.user_id == user_id)
    result = await db.execute(query.order_by(Task.created_at.desc()))
    tasks = result.scalars().unique().all()
    return [_to_out(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await _get_task_with_users(db, task_id)
    return _to_out(task)


@router.patch("/{task_id}", response_model=TaskOut, dependencies=[Depends(require_api_key)])
async def update_task(task_id: uuid.UUID, payload: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await _get_task_with_users(db, task_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    task = await _get_task_with_users(db, task_id)
    await _broadcast("task.updated", task)
    return _to_out(task)


@router.post("/{task_id}/assign", response_model=TaskOut, dependencies=[Depends(require_api_key)])
async def assign_task(task_id: uuid.UUID, payload: TaskAssign, db: AsyncSession = Depends(get_db)):
    task = await _get_task_with_users(db, task_id)
    existing_ids = {a.user_id for a in task.assignments}
    for user_id in payload.user_ids:
        if user_id in existing_ids:
            continue
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(404, f"Utilisateur {user_id} introuvable")
        db.add(TaskAssignment(task_id=task.id, user_id=user_id))
    await db.commit()
    task = await _get_task_with_users(db, task_id)
    await _broadcast("task.updated", task)
    return _to_out(task)


@router.post("/{task_id}/start", response_model=TaskOut, dependencies=[Depends(require_api_key)])
async def start_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await _get_task_with_users(db, task_id)
    now = datetime.now(timezone.utc)
    task.date_debut = now
    task.date_fin_prevue = now + timedelta(minutes=task.minutes_allouees)
    task.statut = TaskStatus.en_cours
    await db.commit()
    task = await _get_task_with_users(db, task_id)
    await _broadcast("task.started", task)
    return _to_out(task)


@router.post("/{task_id}/complete", response_model=TaskOut, dependencies=[Depends(require_api_key)])
async def complete_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await _get_task_with_users(db, task_id)
    task.date_fin_reelle = datetime.now(timezone.utc)
    task.statut = TaskStatus.terminee

    # Points de ponctualité : la tâche est terminée dans le temps qui lui était
    # alloué (voir docs/CONCEPTION.md). Attribués à chaque personne affiliée,
    # cumulés sur User.points pour être consultés depuis le back-office.
    on_time = task.date_fin_prevue is not None and _as_utc(task.date_fin_reelle) <= _as_utc(task.date_fin_prevue)
    if on_time:
        for assignment in task.assignments:
            assignment.user.points += POINTS_PER_ON_TIME_TASK

    await db.commit()
    task = await _get_task_with_users(db, task_id)
    await _broadcast("task.completed", task)
    return _to_out(task)


@router.delete("/{task_id}", status_code=204, dependencies=[Depends(require_api_key)])
async def delete_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Suppression définitive (contrairement à /archive qui est réversible)."""
    task = await _get_task_with_users(db, task_id)
    titre = task.titre
    await db.delete(task)
    await db.commit()
    await manager.broadcast({"type": "task.deleted", "task": {"id": str(task_id), "titre": titre}})


@router.post("/{task_id}/archive", response_model=TaskOut, dependencies=[Depends(require_api_key)])
async def archive_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await _get_task_with_users(db, task_id)
    task.statut = TaskStatus.archivee
    await db.commit()
    task = await _get_task_with_users(db, task_id)
    await _broadcast("task.updated", task)
    return _to_out(task)


@router.post("/{task_id}/restore", response_model=TaskOut, dependencies=[Depends(require_api_key)])
async def restore_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Sort une tâche archivée de l'archive et la remet à zéro (à faire)."""
    task = await _get_task_with_users(db, task_id)
    if task.statut != TaskStatus.archivee:
        raise HTTPException(400, "Seule une tâche archivée peut être restaurée")
    task.statut = TaskStatus.a_faire
    task.date_debut = None
    task.date_fin_prevue = None
    task.date_fin_reelle = None
    await db.commit()
    task = await _get_task_with_users(db, task_id)
    await _broadcast("task.updated", task)
    return _to_out(task)
