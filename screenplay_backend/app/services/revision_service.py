"""
Сервис управления версиями документа (Revision).

Позволяет создавать снапшоты текущего состояния блоков,
просматривать историю версий и восстанавливать предыдущие версии.
Снапшоты хранятся в JSONB для гибкости и простоты восстановления.

При восстановлении создаётся НОВАЯ версия с восстановленным состоянием.
Существующая история не перезаписывается.
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException
from app.models.block import ScriptBlock
from app.models.document import ScriptDocument
from app.models.project import Project
from app.models.revision import Revision
from app.schemas.revision import (
    RevisionCreateRequest,
    RevisionResponse,
    RevisionDetailResponse,
)


class RevisionService:
    """Сервис управления версиями документа."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_revisions(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[RevisionResponse]:
        """Получить список всех версий документа."""
        await self._check_document_access(document_id, user_id)

        result = await self.db.execute(
            select(Revision)
            .where(Revision.document_id == document_id)
            .order_by(Revision.created_at.desc())
        )
        revisions = result.scalars().all()

        return [
            RevisionResponse(
                id=r.id,
                document_id=r.document_id,
                label=r.label,
                change_summary=r.change_summary,
                created_by=r.created_by,
                created_at=r.created_at,
            )
            for r in revisions
        ]

    async def create_revision(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        request: RevisionCreateRequest | None = None,
    ) -> RevisionResponse:
        """Создать новый снапшот текущего состояния документа.

        Сохраняет все блоки документа в виде JSON-снапшота.
        Может быть вызвано автоматически (автосохранение) или
        явно пользователем (именованная версия).
        """
        await self._check_document_access(document_id, user_id)

        # Загружаем все блоки документа
        blocks_result = await self.db.execute(
            select(ScriptBlock)
            .where(ScriptBlock.document_id == document_id)
            .order_by(ScriptBlock.order_index)
        )
        blocks = blocks_result.scalars().all()

        # Формируем снапшот: список блоков в JSON
        snapshot = {
            "blocks": [
                {
                    "id": str(b.id),
                    "order_index": b.order_index,
                    "block_type": b.block_type.value if hasattr(b.block_type, "value") else b.block_type,
                    "text_content": b.text_content,
                    "meta_json": b.meta_json,
                    "scene_number": b.scene_number,
                }
                for b in blocks
            ],
            "block_count": len(blocks),
        }

        label = request.label if request else None
        change_summary = request.change_summary if request else None

        # Автоматическое описание изменений, если не указано явно
        if not change_summary:
            change_summary = f"Автосохранение: {len(blocks)} блоков"

        revision = Revision(
            document_id=document_id,
            label=label,
            snapshot_json=snapshot,
            change_summary=change_summary,
            created_by=user_id,
        )
        self.db.add(revision)
        await self.db.flush()

        # Обновляем current_revision_id в документе
        doc_result = await self.db.execute(
            select(ScriptDocument).where(ScriptDocument.id == document_id)
        )
        doc = doc_result.scalar_one()
        doc.current_revision_id = revision.id
        self.db.add(doc)
        await self.db.flush()

        return RevisionResponse(
            id=revision.id,
            document_id=revision.document_id,
            label=revision.label,
            change_summary=revision.change_summary,
            created_by=revision.created_by,
            created_at=revision.created_at,
        )

    async def get_revision(
        self, revision_id: uuid.UUID, user_id: uuid.UUID
    ) -> RevisionDetailResponse:
        """Получить полные данные версии со снапшотом."""
        result = await self.db.execute(
            select(Revision)
            .join(ScriptDocument, Revision.document_id == ScriptDocument.id)
            .join(Project, ScriptDocument.project_id == Project.id)
            .where(
                Revision.id == revision_id,
                Project.user_id == user_id,
            )
        )
        revision = result.scalar_one_or_none()
        if revision is None:
            raise NotFoundException("Версия не найдена или нет доступа")

        return RevisionDetailResponse(
            id=revision.id,
            document_id=revision.document_id,
            label=revision.label,
            snapshot_json=revision.snapshot_json,
            change_summary=revision.change_summary,
            created_by=revision.created_by,
            created_at=revision.created_at,
        )

    async def restore_revision(
        self, revision_id: uuid.UUID, user_id: uuid.UUID
    ) -> RevisionResponse:
        """Восстановить состояние документа из снапшота версии.

        ВНИМАНИЕ: текущее состояние документа будет ЗАМЕНЕНО.
        Перед восстановлением автоматически создаётся новая версия
        с текущим состоянием, чтобы не потерять историю.
        """
        # Получаем версию для восстановления
        detail = await self.get_revision(revision_id, user_id)

        document_id = detail.document_id

        # Сохраняем текущее состояние перед восстановлением
        await self.create_revision(
            document_id,
            user_id,
            RevisionCreateRequest(
                label=f"auto_before_restore_{revision_id}",
                change_summary="Автоматическая версия перед восстановлением",
            ),
        )

        # Удаляем все текущие блоки документа
        blocks_result = await self.db.execute(
            select(ScriptBlock).where(ScriptBlock.document_id == document_id)
        )
        current_blocks = blocks_result.scalars().all()
        for block in current_blocks:
            await self.db.delete(block)

        # Восстанавливаем блоки из снапшота
        snapshot_blocks = detail.snapshot_json.get("blocks", [])
        from app.models.block import BlockType

        for b_data in snapshot_blocks:
            block = ScriptBlock(
                document_id=document_id,
                order_index=b_data["order_index"],
                block_type=BlockType(b_data["block_type"]),
                text_content=b_data["text_content"],
                meta_json=b_data.get("meta_json", {}),
                scene_number=b_data.get("scene_number"),
            )
            self.db.add(block)

        # Создаём новую версию с восстановленным состоянием
        restored_revision = await self.create_revision(
            document_id,
            user_id,
            RevisionCreateRequest(
                label=f"restored_from_{revision_id}",
                change_summary="Восстановление из предыдущей версии",
            ),
        )

        return restored_revision

    async def create_autosave_revision(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> RevisionResponse | None:
        """Создать версию при автосохранении.

        Создаёт версию только если количество блоков кратно 5
        (каждый 5-й автосейв). Это предотвращает создание слишком
        большого количества мелких версий.
        """
        # Считаем количество блоков
        count_result = await self.db.execute(
            select(func.count()).select_from(
                select(ScriptBlock).where(
                    ScriptBlock.document_id == document_id
                ).subquery()
            )
        )
        block_count = count_result.scalar() or 0

        # Каждый 5-й автосейв или при 0 блоков — не создаём
        if block_count == 0 or block_count % 5 != 0:
            return None

        return await self.create_revision(document_id, user_id)

    async def _check_document_access(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Проверить доступ пользователя к документу."""
        result = await self.db.execute(
            select(ScriptDocument)
            .join(Project, ScriptDocument.project_id == Project.id)
            .where(
                ScriptDocument.id == document_id,
                Project.user_id == user_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundException("Документ не найден или нет доступа")
