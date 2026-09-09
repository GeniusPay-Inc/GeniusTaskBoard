import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserStatus
from app.schemas import UserCreate, UserOut, UserUpdate
from app.security import require_api_key

router = APIRouter(prefix="/api/v1/users", tags=["personnel"])


@router.post("", response_model=UserOut, status_code=201, dependencies=[Depends(require_api_key)])
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(**payload.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("", response_model=list[UserOut])
async def list_users(statut: UserStatus | None = None, db: AsyncSession = Depends(get_db)):
    query = select(User)
    if statut:
        query = query.where(User.statut == statut)
    result = await db.execute(query.order_by(User.nom))
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Personne introuvable")
    return user


@router.patch("/{user_id}", response_model=UserOut, dependencies=[Depends(require_api_key)])
async def update_user(user_id: uuid.UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Personne introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/{user_id}/archive", response_model=UserOut, dependencies=[Depends(require_api_key)])
async def archive_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Personne introuvable")
    user.statut = UserStatus.archive
    await db.commit()
    await db.refresh(user)
    return user
