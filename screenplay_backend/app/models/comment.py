"""
Модель комментария (Comment).

В MVP — заметки автора к документу или конкретному блоку,
не попадающие в финальный экспорт. В будущем — полноценные
комментарии рецензентов и соавторов с разграничением по ролям.
"""

import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    document_id: uuid.UUID = Field(foreign_key="script_documents.id")
    # Если block_id указан — комментарий привязан к конкретному блоку
    # Если null — комментарий ко всему документу
    block_id: uuid.UUID | None = Field(
        foreign_key="script_blocks.id",
        nullable=True,
    )
    user_id: uuid.UUID = Field(foreign_key="users.id")
    text: str = Field()
    resolved_at: datetime | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
