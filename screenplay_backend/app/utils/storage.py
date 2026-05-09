"""
Файловое хранилище для экспортов.

Сохраняет сгенерированные файлы экспорта (PDF, Fountain, TXT)
в файловой системе и предоставляет пути для скачивания.
"""

import os
from pathlib import Path
from datetime import datetime, timezone

from app.config import settings


def ensure_storage_dirs():
    """Убедиться, что директории хранилища существуют."""
    Path(settings.EXPORT_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    Path("./storage/temp").mkdir(parents=True, exist_ok=True)


def get_export_path(export_id: str, extension: str) -> str:
    """Получить путь для сохранения файла экспорта.

    Формат пути: storage/exports/{год}/{месяц}/{export_id}.{расширение}
    """
    now = datetime.now(timezone.utc)
    subdir = os.path.join(
        settings.EXPORT_STORAGE_PATH,
        str(now.year),
        f"{now.month:02d}",
    )
    Path(subdir).mkdir(parents=True, exist_ok=True)
    return os.path.join(subdir, f"{export_id}.{extension}")


def delete_export_file(file_path: str) -> None:
    """Удалить файл экспорта, если он существует."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
