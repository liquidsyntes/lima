"""
Сервис управления проектами.

Реализует CRUD-операции для проектов сценария: создание,
получение списка, обновление, архивирование и дублирование.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundException, ForbiddenException
from app.models.project import Project, ProjectStatus
from app.models.document import ScriptDocument
from app.models.project_settings import ProjectSettings
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
)


class ProjectService:
    """Сервис управления проектами пользователя."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 50, search: str = ""
    ) -> ProjectListResponse:
        """Получить список проектов пользователя с пагинацией и поиском."""
        query = select(Project).where(
            Project.user_id == user_id,
            Project.status == ProjectStatus.ACTIVE,
        )
        if search:
            query = query.where(Project.title.ilike(f"%{search}%"))

        # Подсчёт общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Получение страницы
        query = query.order_by(Project.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        projects = result.scalars().all()

        return ProjectListResponse(
            items=[
                ProjectResponse(
                    id=p.id,
                    user_id=p.user_id,
                    title=p.title,
                    format_type=p.format_type,
                    language=p.language,
                    status=p.status,
                    last_opened_at=p.last_opened_at,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
                for p in projects
            ],
            total=total,
            offset=offset,
            limit=limit,
        )

    async def create_project(
        self, user_id: uuid.UUID, request: ProjectCreateRequest
    ) -> ProjectResponse:
        """Создать новый проект с документом и настройками по умолчанию."""
        project = Project(
            user_id=user_id,
            title=request.title,
            format_type=request.format_type,
            language=request.language,
        )
        self.db.add(project)
        await self.db.flush()

        # Создаём документ для проекта (один к одному в MVP)
        document = ScriptDocument(project_id=project.id)
        self.db.add(document)

        # Создаём настройки проекта по умолчанию
        settings = ProjectSettings(project_id=project.id)
        self.db.add(settings)
        await self.db.flush()

        return ProjectResponse(
            id=project.id,
            user_id=project.user_id,
            title=project.title,
            format_type=project.format_type,
            language=project.language,
            status=project.status,
            last_opened_at=project.last_opened_at,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    async def get_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectResponse:
        """Получить проект по ID с проверкой принадлежности пользователю."""
        project = await self._get_owned_project(project_id, user_id)
        return ProjectResponse(
            id=project.id,
            user_id=project.user_id,
            title=project.title,
            format_type=project.format_type,
            language=project.language,
            status=project.status,
            last_opened_at=project.last_opened_at,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    async def update_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, request: ProjectUpdateRequest
    ) -> ProjectResponse:
        """Обновить проект (название, формат, язык, статус)."""
        project = await self._get_owned_project(project_id, user_id)

        if request.title is not None:
            project.title = request.title
        if request.format_type is not None:
            project.format_type = request.format_type
        if request.language is not None:
            project.language = request.language
        if request.status is not None:
            project.status = request.status

        self.db.add(project)
        await self.db.flush()

        return ProjectResponse(
            id=project.id,
            user_id=project.user_id,
            title=project.title,
            format_type=project.format_type,
            language=project.language,
            status=project.status,
            last_opened_at=project.last_opened_at,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    async def delete_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Мягкое удаление проекта (перевод в архив)."""
        project = await self._get_owned_project(project_id, user_id)
        project.status = ProjectStatus.ARCHIVED
        self.db.add(project)
        await self.db.flush()

    async def duplicate_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectResponse:
        """Дублировать проект со всем содержимым (документ, блоки, настройки)."""
        project = await self._get_owned_project(project_id, user_id)

        # Создаём копию проекта
        new_project = Project(
            user_id=user_id,
            title=f"{project.title} (копия)",
            format_type=project.format_type,
            language=project.language,
        )
        self.db.add(new_project)
        await self.db.flush()

        # Копируем документ
        doc_result = await self.db.execute(
            select(ScriptDocument).where(
                ScriptDocument.project_id == project_id
            )
        )
        old_doc = doc_result.scalar_one_or_none()
        if old_doc:
            new_doc = ScriptDocument(
                project_id=new_project.id,
                title_page_data=old_doc.title_page_data,
                editor_mode=old_doc.editor_mode,
            )
            self.db.add(new_doc)
            await self.db.flush()

            # Копируем блоки из старого документа
            from app.models.block import ScriptBlock

            blocks_result = await self.db.execute(
                select(ScriptBlock)
                .where(ScriptBlock.document_id == old_doc.id)
                .order_by(ScriptBlock.order_index)
            )
            old_blocks = blocks_result.scalars().all()
            for block in old_blocks:
                new_block = ScriptBlock(
                    document_id=new_doc.id,
                    order_index=block.order_index,
                    block_type=block.block_type,
                    text_content=block.text_content,
                    meta_json=block.meta_json,
                    scene_number=block.scene_number,
                )
                self.db.add(new_block)

        # Копируем настройки
        settings_result = await self.db.execute(
            select(ProjectSettings).where(
                ProjectSettings.project_id == project_id
            )
        )
        old_settings = settings_result.scalar_one_or_none()
        if old_settings:
            new_settings = ProjectSettings(
                project_id=new_project.id,
                autosave_interval_seconds=old_settings.autosave_interval_seconds,
                validation_mode=old_settings.validation_mode,
                page_size=old_settings.page_size,
                show_scene_numbers=old_settings.show_scene_numbers,
                dual_dialogue=old_settings.dual_dialogue,
            )
            self.db.add(new_settings)

        await self.db.flush()

        return ProjectResponse(
            id=new_project.id,
            user_id=new_project.user_id,
            title=new_project.title,
            format_type=new_project.format_type,
            language=new_project.language,
            status=new_project.status,
            last_opened_at=new_project.last_opened_at,
            created_at=new_project.created_at,
            updated_at=new_project.updated_at,
        )

    async def _get_owned_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Project:
        """Получить проект с проверкой прав владения.

        Если проект не существует — 404.
        Если проект принадлежит другому пользователю — 403.
        """
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise NotFoundException("Проект не найден")
        if project.user_id != user_id:
            raise ForbiddenException("Нет доступа к этому проекту")

        # Обновляем дату последнего открытия
        project.last_opened_at = datetime.now(timezone.utc)
        self.db.add(project)

        return project
