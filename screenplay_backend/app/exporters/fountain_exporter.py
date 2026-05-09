"""
Экспортёр в Fountain.

Fountain — текстовый формат сценария, основанный на markdown-подобном
синтаксисе. Человекочитаем и легко конвертируется в другие форматы.
Конвертирует структурированные блоки обратно в Fountain-разметку.

Спецификация: https://fountain.io
"""

from app.exporters.base import BaseExporter, ExportOptions
from app.services.formatting.engine import FormattingEngine


class FountainExporter(BaseExporter):
    """Экспортёр сценария в формат Fountain.

    Правила конвертации (из структурированных блоков в Fountain):
    - scene_heading → строка, начинающаяся с INT./EXT./INT./EXT.
      (перед slug line две пустые строки)
    - action → обычный текст
    - character_cue → UPPERCASE строка
    - parenthetical → текст в круглых скобках
    - dialogue → текст после персонажа
    - transition → строка, заканчивающаяся на TO:
    - note → [[текст заметки в двойных квадратных скобках]]
    """

    @property
    def content_type(self) -> str:
        return "text/plain; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return "fountain"

    def export(
        self,
        blocks: list,
        title_page_data: dict | None = None,
        options: ExportOptions | None = None,
    ) -> bytes:
        """Экспортировать сценарий в Fountain.

        Конвертирует структурированные блоки в Fountain-синтаксис
        согласно спецификации формата.
        """
        if options is None:
            options = ExportOptions()

        lines = []

        # Заголовок титульной страницы в Fountain
        if title_page_data and options.include_title_page:
            if title_page_data.get("title"):
                lines.append(f"Title: {title_page_data['title']}")
            if title_page_data.get("author"):
                lines.append(f"Author: {title_page_data['author']}")
            if title_page_data.get("contact"):
                lines.append(f"Contact: {title_page_data['contact']}")
            if title_page_data.get("based_on"):
                lines.append(f"Based on: {title_page_data['based_on']}")
            lines.append("")
            lines.append("===")
            lines.append("")

        prev_type = None

        for block in blocks:
            block_type = block.block_type.value if hasattr(block.block_type, 'value') else block.block_type
            text = block.text_content or ""

            if block_type == "note":
                # Заметки в двойных квадратных скобках — не попадают в финальный экспорт
                lines.append(f"[[{text}]]")
                lines.append("")
                prev_type = block_type
                continue

            if block_type == "scene_heading":
                # Две пустые строки перед slug line (кроме начала документа)
                if prev_type is not None:
                    lines.append("")
                lines.append(text.upper())

            elif block_type == "action":
                lines.append(text)

            elif block_type == "character_cue":
                lines.append(text.upper())

            elif block_type == "parenthetical":
                lines.append(f"({text})")

            elif block_type == "dialogue":
                lines.append(text)

            elif block_type == "transition":
                # Transition должен заканчиваться на TO:
                if not text.upper().rstrip().endswith("TO:"):
                    lines.append(f"{text.upper().rstrip()} TO:")
                else:
                    lines.append(text.upper())

            elif block_type in ("shot", "montage", "end_montage",
                                "flashback_start", "flashback_end",
                                "dream_sequence_start", "dream_sequence_end"):
                lines.append(text.upper())

            elif block_type in ("act_heading", "end_of_act"):
                lines.append("")
                lines.append(text.upper())
                lines.append("")

            else:
                lines.append(text)

            lines.append("")
            prev_type = block_type

        return "\n".join(lines).encode("utf-8")
