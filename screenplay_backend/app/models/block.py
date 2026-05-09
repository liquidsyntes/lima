"""
Модель блока сценария (ScriptBlock).

Каждый абзац в редакторе — это отдельный блок с типом, текстом и мета-данными.
Это не rich-text редактор, а структурированный document editor.
От типа блока зависит его форматирование в редакторе и при экспорте.

Дробная индексация (order_index: float) позволяет вставлять блоки
между существующими без массового переиндексирования: новый блок
получает значение (prev_order + next_order) / 2.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class BlockType(str, Enum):
    """Тип сценарного блока — определяет его форматирование и поведение."""

    SCENE_HEADING = "scene_heading"  # Slug line (INT./EXT. LOCATION - TIME)
    ACTION = "action"  # Описание действия
    CHARACTER_CUE = "character_cue"  # Имя персонажа
    PARENTHETICAL = "parenthetical"  # Ремарка в скобках
    DIALOGUE = "dialogue"  # Реплика
    TRANSITION = "transition"  # Монтажный переход (CUT TO: и т.д.)
    SHOT = "shot"  # Кадр / INSERT / SUPER
    MONTAGE = "montage"  # Начало монтажной последовательности
    END_MONTAGE = "end_montage"  # Конец монтажа
    FLASHBACK_START = "flashback_start"  # Начало флэшбека
    FLASHBACK_END = "flashback_end"  # Конец флэшбека
    DREAM_SEQUENCE_START = "dream_sequence_start"  # Начало сна
    DREAM_SEQUENCE_END = "dream_sequence_end"  # Конец сна
    ACT_HEADING = "act_heading"  # Заголовок акта (телеформат)
    END_OF_ACT = "end_of_act"  # Конец акта (телеформат)
    NOTE = "note"  # Служебная заметка (не попадает в экспорт)


class ScriptBlock(SQLModel, table=True):
    __tablename__ = "script_blocks"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    document_id: uuid.UUID = Field(
        foreign_key="script_documents.id",
        index=True,
    )
    order_index: float = Field(default=0.0)
    block_type: BlockType = Field()
    text_content: str = Field(default="")
    # Мета-данные зависят от типа блока. Примеры:
    # character_cue: {"suffix": "(V.O.)", "is_dual": false}
    # scene_heading: {"time_of_day": "DAY", "is_mini_slug": false}
    # transition: {"transition_type": "CUT TO:"}
    # note: {"author_id": "...", "resolved": false}
    meta_json: dict = Field(default={}, sa_type=JSON)
    scene_number: int | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
