"""
Экспортёр в TXT.

Простой текстовый экспорт сценария с сохранением имён типов блоков
в квадратных скобках для наглядности. Подходит для быстрого просмотра
и обмена текстом без потери структурной информации.
"""

from app.exporters.base import BaseExporter, ExportOptions


class TxtExporter(BaseExporter):
    """Экспортёр сценария в простой текстовый формат.

    Каждый блок выводится с пометкой типа в квадратных скобках
    для сохранения структурной информации в плоском тексте.
    """

    @property
    def content_type(self) -> str:
        return "text/plain; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return "txt"

    # Человекочитаемые названия типов блоков
    TYPE_LABELS: dict[str, str] = {
        "scene_heading": "СЦЕНА",
        "action": "ДЕЙСТВИЕ",
        "character_cue": "ПЕРСОНАЖ",
        "parenthetical": "РЕМАРКА",
        "dialogue": "ДИАЛОГ",
        "transition": "ПЕРЕХОД",
        "shot": "КАДР",
        "montage": "МОНТАЖ",
        "end_montage": "КОНЕЦ МОНТАЖА",
        "flashback_start": "НАЧАЛО ФЛЭШБЕКА",
        "flashback_end": "КОНЕЦ ФЛЭШБЕКА",
        "dream_sequence_start": "НАЧАЛО СНА",
        "dream_sequence_end": "КОНЕЦ СНА",
        "act_heading": "АКТ",
        "end_of_act": "КОНЕЦ АКТА",
        "note": "ЗАМЕТКА",
    }

    def export(
        self,
        blocks: list,
        title_page_data: dict | None = None,
        options: ExportOptions | None = None,
    ) -> bytes:
        """Экспортировать сценарий в TXT с сохранением типов блоков."""
        lines = []

        # Титульная страница
        if title_page_data and options and options.include_title_page:
            lines.append("=" * 60)
            if title_page_data.get("title"):
                lines.append(title_page_data["title"].upper())
            if title_page_data.get("author"):
                lines.append(f"Автор: {title_page_data['author']}")
            if title_page_data.get("contact"):
                lines.append(f"Контакты: {title_page_data['contact']}")
            lines.append("=" * 60)
            lines.append("")

        for block in blocks:
            block_type = block.block_type.value if hasattr(block.block_type, 'value') else block.block_type
            text = block.text_content or ""

            if block_type == "note":
                lines.append(f"[ЗАМЕТКА] {text}")
                lines.append("")
                continue

            label = self.TYPE_LABELS.get(block_type, block_type.upper())
            lines.append(f"[{label}] {text}")
            lines.append("")

        return "\n".join(lines).encode("utf-8")
