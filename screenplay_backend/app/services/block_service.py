"""
Сервис управления блоками сценария.

Реализует CRUD-операции для блоков с дробной индексацией.
Дробная индексация (order_index: float) позволяет вставлять
блоки между существующими без массового переиндексирования:
новый блок получает значение (prev_order + next_order) / 2.

Периодическая нормализация выполняется при обнаружении слишком
близких значений (разница < 0.001).
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException, ForbiddenException
from app.models.block import ScriptBlock, BlockType
from app.models.document import ScriptDocument
from app.models.project import Project
from app.schemas.block import (
    BlockCreateRequest,
    BlockUpdateRequest,
    BlockResponse,
    BlockReorderRequest,
    AutosaveRequest,
)


class BlockService:
    """Сервис управления блоками сценария с дробной индексацией."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_blocks(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[BlockResponse]:
        """Получить все блоки документа в порядке следования."""
        await self._check_document_access(document_id, user_id)

        result = await self.db.execute(
            select(ScriptBlock)
            .where(ScriptBlock.document_id == document_id)
            .order_by(ScriptBlock.order_index)
        )
        blocks = result.scalars().all()

        return [
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
        ]

    async def create_block(
        self, document_id: uuid.UUID, user_id: uuid.UUID, request: BlockCreateRequest
    ) -> BlockResponse:
        """Создать новый блок и вставить его в указанную позицию.

        Если after_block_id не указан, блок добавляется в конец документа.
        """
        await self._check_document_access(document_id, user_id)

        # Вычисляем order_index для нового блока
        order_index = await self._calculate_insert_position(
            document_id, request.after_block_id
        )

        block = ScriptBlock(
            document_id=document_id,
            order_index=order_index,
            block_type=request.block_type,
            text_content=request.text_content,
            meta_json=request.meta_json,
        )
        self.db.add(block)
        await self.db.flush()

        return BlockResponse(
            id=block.id,
            document_id=block.document_id,
            order_index=block.order_index,
            block_type=block.block_type,
            text_content=block.text_content,
            meta_json=block.meta_json,
            scene_number=block.scene_number,
            created_at=block.created_at,
            updated_at=block.updated_at,
        )

    async def update_block(
        self, block_id: uuid.UUID, user_id: uuid.UUID, request: BlockUpdateRequest
    ) -> BlockResponse:
        """Обновить содержимое, тип или мета-данные блока."""
        block = await self._get_accessible_block(block_id, user_id)

        if request.text_content is not None:
            block.text_content = request.text_content
        if request.block_type is not None:
            block.block_type = request.block_type
        if request.meta_json is not None:
            block.meta_json = request.meta_json
        if request.scene_number is not None:
            block.scene_number = request.scene_number

        self.db.add(block)
        await self.db.flush()

        return BlockResponse(
            id=block.id,
            document_id=block.document_id,
            order_index=block.order_index,
            block_type=block.block_type,
            text_content=block.text_content,
            meta_json=block.meta_json,
            scene_number=block.scene_number,
            created_at=block.created_at,
            updated_at=block.updated_at,
        )

    async def delete_block(
        self, block_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Удалить блок из документа."""
        block = await self._get_accessible_block(block_id, user_id)
        await self.db.delete(block)
        await self.db.flush()

    async def reorder_blocks(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        request: BlockReorderRequest,
    ) -> list[BlockResponse]:
        """Переупорядочить блоки согласно новому порядку ID.

        Присваивает блокам новые целочисленные order_index с шагом 1.0,
        начиная с 0. Это также служит нормализацией дробных индексов.
        """
        await self._check_document_access(document_id, user_id)

        for new_index, block_id in enumerate(request.block_ids):
            result = await self.db.execute(
                select(ScriptBlock).where(
                    ScriptBlock.id == block_id,
                    ScriptBlock.document_id == document_id,
                )
            )
            block = result.scalar_one_or_none()
            if block:
                block.order_index = float(new_index)
                self.db.add(block)

        await self.db.flush()

        return await self.get_blocks(document_id, user_id)

    async def autosave(
        self, document_id: uuid.UUID, user_id: uuid.UUID, request: AutosaveRequest
    ) -> dict:
        """Обработать автосохранение — создать/обновить блоки.

        Возвращает статус и флаг, была ли создана новая версия.
        """
        await self._check_document_access(document_id, user_id)

        for block_req in request.blocks:
            order_index = await self._calculate_insert_position(
                document_id, block_req.after_block_id
            )
            block = ScriptBlock(
                document_id=document_id,
                order_index=order_index,
                block_type=block_req.block_type,
                text_content=block_req.text_content,
                meta_json=block_req.meta_json,
            )
            self.db.add(block)

        await self.db.flush()

        # Считаем количество блоков — каждый 5-й автосейв создаёт версию
        count_result = await self.db.execute(
            select(func.count()).select_from(
                select(ScriptBlock).where(
                    ScriptBlock.document_id == document_id
                ).subquery()
            )
        )
        block_count = count_result.scalar() or 0
        should_create_revision = block_count % 5 == 0

        return {
            "saved": True,
            "revision_created": should_create_revision,
            "block_count": block_count,
        }

    async def _calculate_insert_position(
        self, document_id: uuid.UUID, after_block_id: uuid.UUID | None
    ) -> float:
        """Вычислить order_index для вставки нового блока.

        Если after_block_id указан — вставить после него с дробным индексом.
        Если нет — добавить в конец с целым индексом.
        Использует дробную индексацию для вставки без переиндексации.
        """
        if after_block_id:
            # Получаем блок, после которого вставляем
            result = await self.db.execute(
                select(ScriptBlock).where(
                    ScriptBlock.id == after_block_id,
                    ScriptBlock.document_id == document_id,
                )
            )
            prev_block = result.scalar_one_or_none()
            if prev_block is None:
                raise NotFoundException("Блок для вставки не найден")

            prev_order = prev_block.order_index

            # Находим следующий блок
            result = await self.db.execute(
                select(ScriptBlock)
                .where(
                    ScriptBlock.document_id == document_id,
                    ScriptBlock.order_index > prev_order,
                )
                .order_by(ScriptBlock.order_index)
                .limit(1)
            )
            next_block = result.scalar_one_or_none()

            if next_block:
                next_order = next_block.order_index
                new_order = (prev_order + next_order) / 2.0
                # Если индексы слишком близки — нормализуем весь документ
                if (next_order - prev_order) < 0.001:
                    await self._normalize_order_indexes(document_id)
                    # После нормализации пересчитываем позицию
                    new_order = prev_order + 0.5
                return new_order
            else:
                return prev_order + 1.0
        else:
            # Добавляем в конец документа
            result = await self.db.execute(
                select(func.max(ScriptBlock.order_index)).where(
                    ScriptBlock.document_id == document_id
                )
            )
            max_order = result.scalar() or -1.0
            return max_order + 1.0

    async def _normalize_order_indexes(self, document_id: uuid.UUID) -> None:
        """Нормализовать индексы всех блоков документа.

        Присваивает целочисленные значения 0, 1, 2, ... всем блокам
        для предотвращения потери точности float при дробной индексации.
        """
        result = await self.db.execute(
            select(ScriptBlock)
            .where(ScriptBlock.document_id == document_id)
            .order_by(ScriptBlock.order_index)
        )
        blocks = result.scalars().all()
        for i, block in enumerate(blocks):
            block.order_index = float(i)
            self.db.add(block)

    async def _check_document_access(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Проверить, что пользователь имеет доступ к документу."""
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

    async def _get_accessible_block(
        self, block_id: uuid.UUID, user_id: uuid.UUID
    ) -> ScriptBlock:
        """Получить блок с проверкой доступа через документ и проект."""
        result = await self.db.execute(
            select(ScriptBlock)
            .join(ScriptDocument, ScriptBlock.document_id == ScriptDocument.id)
            .join(Project, ScriptDocument.project_id == Project.id)
            .where(
                ScriptBlock.id == block_id,
                Project.user_id == user_id,
            )
        )
        block = result.scalar_one_or_none()
        if block is None:
            raise NotFoundException("Блок не найден или нет доступа")
        return block
