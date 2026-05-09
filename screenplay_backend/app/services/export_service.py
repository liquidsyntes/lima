"""
Сервис экспорта сценария.

Координирует процесс экспорта: создаёт задачу ExportJob,
запускает соответствующий экспортёр (PDF/Fountain/TXT),
сохраняет результат в файловое хранилище и обновляет статус.

В MVP экспорт выполняется синхронно. В будущем — асинхронно
через Celery/RQ для больших документов.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException
from app.models.document import ScriptDocument
from app.models.export_job import ExportJob, ExportType, ExportStatus
from app.models.project import Project
from app.exporters.pdf_exporter import PDFExporter
from app.exporters.fountain_exporter import FountainExporter
from app.exporters.txt_exporter import TxtExporter
from app.exporters.base import ExportOptions
from app.utils.storage import get_export_path


class ExportService:
    """Сервис экспорта сценариев в различные форматы."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_pdf(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict:
        """Запустить экспорт в PDF."""
        return await self._export(document_id, user_id, ExportType.PDF)

    async def export_fountain(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict:
        """Запустить экспорт в Fountain."""
        return await self._export(document_id, user_id, ExportType.FOUNTAIN)

    async def export_txt(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict:
        """Запустить экспорт в TXT."""
        return await self._export(document_id, user_id, ExportType.TXT)

    async def _export(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        export_type: ExportType,
    ) -> dict:
        """Общий метод экспорта.

        Получает все блоки документа, запускает экспортёр
        и сохраняет результат в файл. В MVP — синхронно.
        """
        # Проверяем доступ к документу
        doc_result = await self.db.execute(
            select(ScriptDocument)
            .join(Project, ScriptDocument.project_id == Project.id)
            .where(
                ScriptDocument.id == document_id,
                Project.user_id == user_id,
            )
        )
        doc = doc_result.scalar_one_or_none()
        if doc is None:
            raise NotFoundException("Документ не найден или нет доступа")

        # Загружаем блоки
        from app.models.block import ScriptBlock

        blocks_result = await self.db.execute(
            select(ScriptBlock)
            .where(ScriptBlock.document_id == document_id)
            .order_by(ScriptBlock.order_index)
        )
        blocks = blocks_result.scalars().all()

        # Создаём задачу экспорта
        job = ExportJob(
            document_id=document_id,
            export_type=export_type,
            status=ExportStatus.PROCESSING,
        )
        self.db.add(job)
        await self.db.flush()

        try:
            # Выбираем экспортёр
            exporter_map = {
                ExportType.PDF: (PDFExporter, "pdf"),
                ExportType.FOUNTAIN: (FountainExporter, "fountain"),
                ExportType.TXT: (TxtExporter, "txt"),
            }
            exporter_cls, extension = exporter_map[export_type]

            exporter = exporter_cls()
            options = ExportOptions(
                page_size="letter",
                include_title_page=True,
                include_page_numbers=True,
            )

            file_bytes = exporter.export(
                blocks=blocks,
                title_page_data=doc.title_page_data,
                options=options,
            )

            # Сохраняем файл
            file_path = get_export_path(str(job.id), extension)
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            job.status = ExportStatus.COMPLETED
            job.file_path = file_path
            job.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            job.status = ExportStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)

        self.db.add(job)
        await self.db.flush()

        return {
            "id": str(job.id),
            "document_id": str(job.document_id),
            "export_type": job.export_type.value,
            "status": job.status.value,
            "file_path": job.file_path,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }

    async def get_export_status(
        self, export_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict:
        """Получить статус задачи экспорта."""
        result = await self.db.execute(
            select(ExportJob)
            .join(ScriptDocument, ExportJob.document_id == ScriptDocument.id)
            .join(Project, ScriptDocument.project_id == Project.id)
            .where(
                ExportJob.id == export_id,
                Project.user_id == user_id,
            )
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundException("Задача экспорта не найдена")

        return {
            "id": str(job.id),
            "document_id": str(job.document_id),
            "export_type": job.export_type.value,
            "status": job.status.value,
            "file_path": job.file_path,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
