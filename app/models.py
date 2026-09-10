import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    employe = "employe"


class UserStatus(str, enum.Enum):
    actif = "actif"
    archive = "archive"


class TaskStatus(str, enum.Enum):
    a_faire = "a_faire"
    en_cours = "en_cours"
    terminee = "terminee"
    en_retard = "en_retard"
    archivee = "archivee"


class TaskSource(str, enum.Enum):
    manuel = "manuel"
    api = "api"
    arduino = "arduino"


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    nom: Mapped[str] = mapped_column(String(120), nullable=False)
    prenom: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.employe)
    statut: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.actif)
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    assignments: Mapped[list["TaskAssignment"]] = relationship(back_populates="user", passive_deletes=True)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    titre: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    minutes_allouees: Mapped[int] = mapped_column(Integer, nullable=False)
    statut: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.a_faire)
    source: Mapped[TaskSource] = mapped_column(Enum(TaskSource), default=TaskSource.manuel)

    date_debut: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_fin_prevue: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_fin_reelle: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    assignments: Mapped[list["TaskAssignment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped["Task"] = relationship(back_populates="assignments")
    user: Mapped["User"] = relationship(back_populates="assignments")
