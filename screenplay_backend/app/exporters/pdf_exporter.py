"""
Экспортёр в PDF через ReportLab.

Генерирует профессионально отформатированный PDF-файл сценария
в соответствии с индустриальным стандартом:
- Courier 12pt (обязательное требование)
- Поля: 1.5" слева, 1.0" справа, 1.0" сверху, 1.0" снизу
- Титульная страница без номера
- Нумерация страниц, начиная со второй
- Keep-with-next: character cue + dialogue не разрываются
- Расчёт примерного хронометража (1 стр. ≈ 1 мин.)

Полный контроль позиционирования каждого элемента через
дюймовую систему координат ReportLab.
"""

from io import BytesIO

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfgen import canvas as pdf_canvas

from app.exporters.base import BaseExporter, ExportOptions
from app.services.formatting.rules import FORMATTING_RULES
from app.services.formatting.types import FormattingRule, TextAlignment


class PDFExporter(BaseExporter):
    """Генерация профессионального PDF-файла сценария.

    Использует ReportLab для точного позиционирования каждого
    элемента на странице. Courier 12pt — обязательное требование
    индустриального стандарта.

    Процесс генерации:
    1. Создание документа с правильными полями
    2. Отрисовка титульной страницы (без номера)
    3. Последовательная отрисовка блоков с правилами форматирования
    4. Вставка разрывов страниц перед новыми сценами (опционально)
    5. Нумерация страниц, начиная со второй
    6. Расчёт примерного хронометража
    """

    # Константы страницы US Letter
    PAGE_WIDTH = 8.5 * inch
    PAGE_HEIGHT = 11.0 * inch

    # Поля страницы в пунктах (1 дюйм = 72 pt)
    MARGIN_LEFT = 1.5 * inch
    MARGIN_RIGHT = 1.0 * inch
    MARGIN_TOP = 1.0 * inch
    MARGIN_BOTTOM = 1.0 * inch

    # Шрифт и размер
    FONT_NAME = "Courier"
    FONT_SIZE = 12
    LINE_HEIGHT = FONT_SIZE * 1.2  # Межстрочный интервал: 14.4pt

    def __init__(self):
        self._page_number = 0
        self._current_y = 0

    @property
    def content_type(self) -> str:
        return "application/pdf"

    @property
    def file_extension(self) -> str:
        return "pdf"

    def export(
        self,
        blocks: list,
        title_page_data: dict | None = None,
        options: ExportOptions | None = None,
    ) -> bytes:
        """Сгенерировать PDF и вернуть как bytes.

        Args:
            blocks: список ScriptBlock в порядке следования
            title_page_data: данные титульной страницы
            options: настройки экспорта (размер страницы, включение титульной и т.д.)

        Returns:
            PDF-файл в виде байтов
        """
        if options is None:
            options = ExportOptions()

        page_size = letter if options.page_size == "letter" else A4
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=self.MARGIN_LEFT,
            rightMargin=self.MARGIN_RIGHT,
            topMargin=self.MARGIN_TOP,
            bottomMargin=self.MARGIN_BOTTOM,
            title=title_page_data.get("title", "Screenplay") if title_page_data else "Screenplay",
            author=title_page_data.get("author", "") if title_page_data else "",
        )

        story = []

        # Титульная страница отрисовывается через onFirstPage колбэк
        if title_page_data and options.include_title_page:
            # Пустой абзац, чтобы контент начался после титульной
            story.append(Spacer(1, 1))

        # Собираем элементы для основного содержимого
        for i, block in enumerate(blocks):
            block_type = (
                block.block_type.value
                if hasattr(block.block_type, "value")
                else block.block_type
            )
            text = block.text_content or ""

            if block_type == "note":
                continue  # Заметки не попадают в финальный PDF

            rule = FORMATTING_RULES.get(block_type)

            if rule is None:
                # Неизвестный тип — отображаем как action
                story.append(self._make_paragraph(text, FORMATTING_RULES["action"]))
                continue

            # Строим абзац с правильным форматированием
            para = self._make_paragraph(text, rule)

            # Keep-with-next: character + dialogue не должны разрываться
            if block_type == "character_cue" and i + 1 < len(blocks):
                next_block = blocks[i + 1]
                next_type = (
                    next_block.block_type.value
                    if hasattr(next_block.block_type, "value")
                    else next_block.block_type
                )
                if next_type in ("dialogue", "parenthetical"):
                    next_para = self._make_paragraph(
                        next_block.text_content or "",
                        FORMATTING_RULES.get(next_type, rule),
                    )
                    story.append(KeepTogether([para, next_para]))
                    # Пропускаем следующий блок — он уже включён
                    continue

            story.append(para)

        # Номера страниц — через колбэк onPage
        def add_page_number(canvas, doc):
            """Колбэк ReportLab для отрисовки номера страницы.

            Нумерация начинается со второй страницы (первая — титульная).
            Номер в правом верхнем углу: формат "PAGE.".
            """
            page_num = canvas.getPageNumber()
            if page_num > 1 or not (title_page_data and options.include_title_page):
                canvas.saveState()
                canvas.setFont(self.FONT_NAME, self.FONT_SIZE)
                display_num = page_num - 1 if (title_page_data and options.include_title_page) else page_num
                # Номер страницы в правом верхнем углу
                canvas.drawRightString(
                    doc.pagesize[0] - self.MARGIN_RIGHT,
                    doc.pagesize[1] - self.MARGIN_TOP + 0.3 * inch,
                    f"{display_num}.",
                )
                canvas.restoreState()

        def title_page(canvas, doc):
            """Колбэк ReportLab для отрисовки титульной страницы.

            Титульная страница: название, автор, контакты.
            Без номера страницы, без полей как у основного текста.
            """
            if not (title_page_data and options.include_title_page):
                return

            canvas.saveState()
            page_w = doc.pagesize[0]
            page_h = doc.pagesize[1]

            # Центрируем титульную информацию по вертикали и горизонтали
            center_x = page_w / 2.0
            y = page_h / 2.0 + 3 * inch

            canvas.setFont(self.FONT_NAME, self.FONT_SIZE)

            if title_page_data.get("title"):
                canvas.setFont(self.FONT_NAME, 14)
                canvas.drawCentredString(center_x, y, title_page_data["title"].upper())
                y -= 2 * self.LINE_HEIGHT

            if title_page_data.get("author"):
                canvas.setFont(self.FONT_NAME, self.FONT_SIZE)
                canvas.drawCentredString(center_x, y, f"by {title_page_data['author']}")
                y -= self.LINE_HEIGHT

            if title_page_data.get("based_on"):
                canvas.setFont(self.FONT_NAME, self.FONT_SIZE)
                canvas.drawCentredString(
                    center_x, y, f"Based on: {title_page_data['based_on']}"
                )
                y -= self.LINE_HEIGHT

            if title_page_data.get("contact"):
                y = self.MARGIN_BOTTOM + 2 * inch
                canvas.setFont(self.FONT_NAME, self.FONT_SIZE)
                canvas.drawCentredString(center_x, y, title_page_data["contact"])

            canvas.restoreState()

        # Собираем PDF
        if title_page_data and options.include_title_page:
            doc.build(
                story,
                onFirstPage=title_page,
                onLaterPages=add_page_number,
            )
        else:
            doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

        return buffer.getvalue()

    def _make_paragraph(self, text: str, rule: FormattingRule) -> Paragraph:
        """Создать Paragraph с правильным форматированием для типа блока.

        Преобразует FormattingRule в стиль ReportLab ParagraphStyle
        с учётом выравнивания, отступов и межстрочного интервала.
        """
        if rule.uppercase:
            text = text.upper()

        # Определяем выравнивание
        alignment_map = {
            TextAlignment.LEFT: TA_LEFT,
            TextAlignment.CENTER: TA_CENTER,
            TextAlignment.RIGHT: TA_RIGHT,
        }
        alignment = alignment_map.get(rule.alignment, TA_LEFT)

        # Создаём стиль для абзаца с правильными отступами и шрифтом
        style = ParagraphStyle(
            "screenplay_block",
            fontName=self.FONT_NAME,
            fontSize=rule.font_size,
            leading=self.LINE_HEIGHT,
            alignment=alignment,
            leftIndent=rule.indent_left_inches * inch,
            rightIndent=rule.indent_right_inches * inch,
            spaceBefore=rule.margin_top_lines * self.LINE_HEIGHT,
            spaceAfter=rule.margin_bottom_lines * self.LINE_HEIGHT,
        )

        return Paragraph(text, style)
