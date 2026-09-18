import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TaskSource, TaskStatus, UserRole, UserStatus


# ---------- User ----------

class UserCreate(BaseModel):
    nom: str
    prenom: str
    role: UserRole = UserRole.employe


class UserUpdate(BaseModel):
    nom: str | None = None
    prenom: str | None = None
    role: UserRole | None = None
    statut: UserStatus | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nom: str
    prenom: str
    role: UserRole
    statut: UserStatus
    photo_url: str | None = None
    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def force_utc(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


# ---------- Task ----------

class TaskCreate(BaseModel):
    titre: str
    description: str | None = None
    minutes_allouees: int = Field(gt=0)
    source: TaskSource = TaskSource.manuel
    user_ids: list[uuid.UUID] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    titre: str | None = None
    description: str | None = None
    minutes_allouees: int | None = Field(default=None, gt=0)
    statut: TaskStatus | None = None


class TaskAssign(BaseModel):
    user_ids: list[uuid.UUID]


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    titre: str
    description: str | None
    minutes_allouees: int
    statut: TaskStatus
    source: TaskSource
    date_debut: datetime | None
    date_fin_prevue: datetime | None
    date_fin_reelle: datetime | None
    created_at: datetime
    updated_at: datetime
    assigned_users: list[UserOut] = Field(default_factory=list)

    @field_validator("date_debut", "date_fin_prevue", "date_fin_reelle", "created_at", "updated_at", mode="after")
    @classmethod
    def force_utc(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


# ---------- WebSocket events ----------

class WSEvent(BaseModel):
    type: str
    task: TaskOut | None = None
    user: UserOut | None = None
