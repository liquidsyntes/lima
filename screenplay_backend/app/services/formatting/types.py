"""
Типы данных движка форматирования.

Определяют структуру правил форматирования для каждого типа
сценарного блока. Значения в дюймах, так как экспорт в PDF
и индустриальный стандарт требуют дюймовой точности.
"""

from enum import Enum

from pydantic import BaseModel


class TextAlignment(str, Enum):
    """Выравнивание текста в блоке."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class FormattingRule(BaseModel):
    """Правило форматирования для одного типа сценарного блока.

    Содержит все параметры, необходимые для корректного отображения
    и экспорта блока данного типа. Отступы указаны в дюймах,
    так как индустриальный стандарт (Final Draft, Fade In)
    и PDF используют дюймовую систему координат.

    Поля:
    - uppercase: весь текст должен быть в верхнем регистре
    - alignment: выравнивание текста (left/center/right)
    - indent_left_inches: отступ слева в дюймах
    - indent_right_inches: отступ справа в дюймах
    - margin_top_lines: пустых строк перед блоком
    - margin_bottom_lines: пустых строк после блока
    - max_lines: рекомендуемая максимальная длина блока в строках
    - max_characters_per_line: максимальная ширина строки в символах
    - font_size: размер шрифта в пунктах (Courier 12pt — стандарт)
    """

    block_type: str
    uppercase: bool = False
    alignment: TextAlignment = TextAlignment.LEFT
    indent_left_inches: float = 0.0
    indent_right_inches: float = 0.0
    margin_top_lines: int = 0
    margin_bottom_lines: int = 0
    max_lines: int | None = None
    max_characters_per_line: int | None = None
    font_size: int = 12
    bold: bool = False
    underline: bool = False
