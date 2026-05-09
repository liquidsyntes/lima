"""
Модель проекта сценария.

Пользователь может иметь множество проектов.
format_type определяет шаблон страниц и правила форматирования:
полный метр, эпизод сериала, короткий метр, веб-сериал.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class ProjectFormatType(str, Enum):
    """Тип формата сценария."""

    FEATURE_FILM = "feature_film"  # Полный метр
    TV_EPISODE = "tv_episode"  # Эпизод сериала
    SHORT_FILM = "short_film"  # Короткий метр
    WEB_SERIES = "web_series"  # Веб-сериал


class ProjectStatus(str, Enum):
    """Статус проекта."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        index=True,
    )
    title: str = Field(max_length=500)
    format_type: ProjectFormatType = Field(
        default=ProjectFormatType.FEATURE_FILM,
    )
    language: str = Field(default="en", max_length=10)
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE)
    last_opened_at: datetime | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
