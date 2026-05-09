"""
Эндпоинты управления документом сценария API v1.

Обрабатывают получение документа (с блоками и без), обновление
метаданных, автосохранение блоков, валидацию, структуру и экспорт.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentFullResponse,
    DocumentUpdateRequest,
)
from app.schemas.block import (
    BlockCreateRequest,
    BlockResponse,
    BlockReorderRequest,
    AutosaveRequest,
)
from app.schemas.validation import ValidationResponse
from app.schemas.export import ExportResponse
from app.schemas.revision import (
    RevisionCreateRequest,
    RevisionResponse,
    RevisionDetailResponse,
)
from app.services.document_service import DocumentService
from app.services.block_service import BlockService
from app.services.validation.engine import ValidationEngine
from app.services.scene_service import SceneService

router = APIRouter(prefix="/documents", tags=["Документы"])


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить документ по ID (без блоков)."""
    service = DocumentService(db)
    return await service.get_document(document_id, current_user.id)


@router.get("/{document_id}/full", response_model=DocumentFullResponse)
async def get_document_full(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить документ со всеми блоками в порядке следования."""
    service = DocumentService(db)
    return await service.get_document_full(document_id, current_user.id)


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    request: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить метаданные документа (титульная страница, режим редактора)."""
    service = DocumentService(db)
    return await service.update_document(document_id, current_user.id, request)


@router.get("/{document_id}/blocks", response_model=list[BlockResponse])
async def get_blocks(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить все блоки документа в порядке следования."""
    service = BlockService(db)
    return await service.get_blocks(document_id, current_user.id)


@router.post("/{document_id}/blocks", response_model=BlockResponse, status_code=201)
async def create_block(
    document_id: uuid.UUID,
    request: BlockCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать новый блок в документе."""
    service = BlockService(db)
    return await service.create_block(document_id, current_user.id, request)


@router.post("/{document_id}/blocks/reorder", response_model=list[BlockResponse])
async def reorder_blocks(
    document_id: uuid.UUID,
    request: BlockReorderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Переупорядочить блоки документа."""
    service = BlockService(db)
    return await service.reorder_blocks(document_id, current_user.id, request)


@router.post("/{document_id}/autosave")
async def autosave(
    document_id: uuid.UUID,
    request: AutosaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Автосохранение блоков документа.

    Принимает массив изменённых блоков и сохраняет их.
    Каждый 5-й автосейв автоматически создаёт новую версию.
    """
    service = BlockService(db)
    return await service.autosave(document_id, current_user.id, request)


@router.post("/{document_id}/validate")
async def validate_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Запустить проверку сценарных правил форматирования.

    Возвращает список предупреждений по всем блокам документа.
    Режим проверки зависит от editor_mode документа (draft/professional).
    """
    from app.models.block import ScriptBlock, BlockType

    doc_service = DocumentService(db)
    doc = await doc_service.get_document(document_id, current_user.id)

    block_service = BlockService(db)
    blocks = await block_service.get_blocks(document_id, current_user.id)

    # Преобразуем BlockResponse в объекты ScriptBlock для валидатора
    validation_blocks = []
    for b in blocks:
        validation_blocks.append(
            ScriptBlock(
                id=b.id,
                document_id=b.document_id,
                order_index=b.order_index,
                block_type=BlockType(b.block_type.value),
                text_content=b.text_content,
                meta_json=b.meta_json,
                scene_number=b.scene_number,
            )
        )

    engine = ValidationEngine()
    result = engine.validate(validation_blocks, mode=doc.editor_mode.value)
    return result


@router.get("/{document_id}/structure")
async def get_document_structure(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить структуру документа: сцены, акты, статистику.

    Используется для панели навигации по сценам в редакторе.
    """
    from app.models.block import ScriptBlock, BlockType

    doc_service = DocumentService(db)
    await doc_service.get_document(document_id, current_user.id)

    block_service = BlockService(db)
    blocks = await block_service.get_blocks(document_id, current_user.id)

    # Преобразуем BlockResponse в объекты ScriptBlock для SceneService
    structure_blocks = []
    for b in blocks:
        structure_blocks.append(
            ScriptBlock(
                id=b.id,
                document_id=b.document_id,
                order_index=b.order_index,
                block_type=BlockType(b.block_type.value),
                text_content=b.text_content,
                meta_json=b.meta_json,
                scene_number=b.scene_number,
            )
        )

    return SceneService.extract_structure(structure_blocks)
