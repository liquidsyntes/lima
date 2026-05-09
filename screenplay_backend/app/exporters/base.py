"""
Абстрактный базовый класс для всех экспортёров.

Определяет общий интерфейс экспорта: каждый экспортёр должен
реализовать метод export(), принимающий список блоков и
опциональные метаданные, и возвращающий результат экспорта.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class ExportOptions(BaseModel):
    """Общие настройки экспорта."""

    page_size: str = "letter"  # letter или a4
    include_title_page: bool = True
    include_page_numbers: bool = True
    include_scene_numbers: bool = True


class BaseExporter(ABC):
    """Базовый класс для всех экспортёров сценария."""

    @abstractmethod
    def export(
        self,
        blocks: list,
        title_page_data: dict | None = None,
        options: ExportOptions | None = None,
    ) -> bytes:
        """Экспортировать сценарий в целевой формат.

        Args:
            blocks: список ScriptBlock в порядке следования
            title_page_data: данные титульной страницы (title, author, contact, ...)
            options: настройки экспорта

        Returns:
            Байтовое представление готового файла
        """
        ...

    @property
    @abstractmethod
    def content_type(self) -> str:
        """MIME-тип генерируемого файла."""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Расширение генерируемого файла."""
        ...
