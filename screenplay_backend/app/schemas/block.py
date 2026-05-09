"""
Схемы для управления блоками сценария.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.block import BlockType


class BlockCreateRequest(BaseModel):
    """Запрос на создание нового блока в документе."""

    block_type: BlockType
    text_content: str = ""
    meta_json: dict = {}
    after_block_id: uuid.UUID | None = None  # Вставить после указанного блока


class BlockUpdateRequest(BaseModel):
    """Запрос на обновление существующего блока."""

    text_content: str | None = None
    block_type: BlockType | None = None
    meta_json: dict | None = None
    scene_number: int | None = None


class BlockResponse(BaseModel):
    """Ответ с данными блока сценария."""

    id: uuid.UUID
    document_id: uuid.UUID
    order_index: float
    block_type: BlockType
    text_content: str
    meta_json: dict
    scene_number: int | None
    created_at: datetime
    updated_at: datetime


class BlockReorderRequest(BaseModel):
    """Запрос на переупорядочивание блоков."""

    block_ids: list[uuid.UUID]  # Список ID блоков в новом порядке


class AutosaveRequest(BaseModel):
    """Запрос автосохранения — массив изменённых блоков."""

    blocks: list[BlockCreateRequest]
