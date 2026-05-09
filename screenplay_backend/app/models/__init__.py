"""
Реэкспорт всех моделей для Alembic.

При импорте этого пакета все SQLModel-классы регистрируются
в SQLModel.metadata, что позволяет Alembic автоматически
обнаруживать изменения схемы.
"""

from app.models.user import User
from app.models.project import Project, ProjectFormatType, ProjectStatus
from app.models.document import ScriptDocument, EditorMode
from app.models.block import ScriptBlock, BlockType
from app.models.revision import Revision
from app.models.export_job import ExportJob, ExportType, ExportStatus
from app.models.comment import Comment
from app.models.project_settings import ProjectSettings

__all__ = [
    "User",
    "Project",
    "ProjectFormatType",
    "ProjectStatus",
    "ScriptDocument",
    "EditorMode",
    "ScriptBlock",
    "BlockType",
    "Revision",
    "ExportJob",
    "ExportType",
    "ExportStatus",
    "Comment",
    "ProjectSettings",
]
