"""
Сервис управления документами сценария.

Обрабатывает получение и обновление метаданных документа:
данные титульной страницы, режим редактора.
Получение блоков документа делегируется в BlockService.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException, ForbiddenException
from app.models.document import ScriptDocument
from app.models.project import Project
from app.schemas.document import (
    DocumentResponse,
    DocumentFullResponse,
    DocumentUpdateRequest,
)
from app.schemas.block import BlockResponse


class DocumentService:
    """Сервис управления документом сценария."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_document(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> DocumentResponse:
        """Получить документ без блоков."""
        doc = await self._get_accessible_document(document_id, user_id)
        return DocumentResponse(
            id=doc.id,
            project_id=doc.project_id,
            title_page_data=doc.title_page_data,
            current_revision_id=doc.current_revision_id,
            editor_mode=doc.editor_mode,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    async def get_document_full(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> DocumentFullResponse:
        """Получить документ со всеми блоками в порядке следования."""
        doc = await self._get_accessible_document(document_id, user_id)

        from app.models.block import ScriptBlock

        result = await self.db.execute(
            select(ScriptBlock)
            .where(ScriptBlock.document_id == document_id)
            .order_by(ScriptBlock.order_index)
        )
        blocks = result.scalars().all()

        return DocumentFullResponse(
            id=doc.id,
            project_id=doc.project_id,
            title_page_data=doc.title_page_data,
            current_revision_id=doc.current_revision_id,
            editor_mode=doc.editor_mode,
            blocks=[
                BlockResponse(
                    id=b.id,
                    document_id=b.document_id,
                    order_index=b.order_index,
                    block_type=b.block_type,
                    text_content=b.text_content,
                    meta_json=b.meta_json,
                    scene_number=b.scene_number,
                    created_at=b.created_at,
                    updated_at=b.updated_at,
                )
                for b in blocks
            ],
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    async def update_document(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        request: DocumentUpdateRequest,
    ) -> DocumentResponse:
        """Обновить метаданные документа (титульная страница, режим редактора)."""
        doc = await self._get_accessible_document(document_id, user_id)

        if request.title_page_data is not None:
            doc.title_page_data = request.title_page_data
        if request.editor_mode is not None:
            doc.editor_mode = request.editor_mode

        self.db.add(doc)
        await self.db.flush()

        return DocumentResponse(
            id=doc.id,
            project_id=doc.project_id,
            title_page_data=doc.title_page_data,
            current_revision_id=doc.current_revision_id,
            editor_mode=doc.editor_mode,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    async def _get_accessible_document(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> ScriptDocument:
        """Получить документ с проверкой доступа через проект.

        Убеждается, что документ существует и принадлежит проекту
        текущего пользователя. Если нет — выбрасывает исключение.
        """
        result = await self.db.execute(
            select(ScriptDocument)
            .join(Project, ScriptDocument.project_id == Project.id)
            .where(
                ScriptDocument.id == document_id,
                Project.user_id == user_id,
            )
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundException("Документ не найден или нет доступа")
        return doc

    async def get_document_id_by_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> uuid.UUID:
        """Получить ID документа по ID проекта с проверкой доступа."""
        result = await self.db.execute(
            select(ScriptDocument)
            .join(Project, ScriptDocument.project_id == Project.id)
            .where(
                ScriptDocument.project_id == project_id,
                Project.user_id == user_id,
            )
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundException("Документ не найден или нет доступа")
        return doc.id
