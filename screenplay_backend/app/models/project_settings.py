"""
Модель настроек проекта (ProjectSettings).

Связь "один к одному" с проектом. Хранит пользовательские
предпочтения: интервал автосохранения, режим валидации,
размер страницы и другие параметры редактора.
"""

import uuid

from sqlmodel import Field, SQLModel


class ProjectSettings(SQLModel, table=True):
    __tablename__ = "project_settings"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    project_id: uuid.UUID = Field(
        foreign_key="projects.id",
        unique=True,
    )
    # Интервал автосохранения в секундах (от 5 до 300)
    autosave_interval_seconds: int = Field(default=30, ge=5, le=300)
    # Режим валидации: "draft" (мягкий) или "professional" (строгий)
    validation_mode: str = Field(default="draft")
    # Размер страницы для экспорта: letter (США) или a4
    page_size: str = Field(default="letter")
    # Показывать номера сцен в редакторе
    show_scene_numbers: bool = Field(default=True)
    # Поддержка dual dialogue (два персонажа говорят одновременно)
    dual_dialogue: bool = Field(default=False)
