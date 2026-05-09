"""
Эндпоинты управления отдельными блоками API v1.

Позволяют обновлять и удалять конкретные блоки по их ID.
Массовые операции с блоками — через documents.py.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.block import BlockUpdateRequest, BlockResponse
from app.services.block_service import BlockService

router = APIRouter(prefix="/blocks", tags=["Блоки"])


@router.patch("/{block_id}", response_model=BlockResponse)
async def update_block(
    block_id: uuid.UUID,
    request: BlockUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить блок (текст, тип, мета-данные)."""
    service = BlockService(db)
    return await service.update_block(block_id, current_user.id, request)


@router.delete("/{block_id}", status_code=204)
async def delete_block(
    block_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить блок из документа."""
    service = BlockService(db)
    await service.delete_block(block_id, current_user.id)
