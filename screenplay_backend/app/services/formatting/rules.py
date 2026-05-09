"""
Правила форматирования для всех типов сценарных блоков.

Каждое правило определяет визуальные параметры блока в редакторе
и при экспорте: выравнивание, отступы в дюймах, регистр текста,
рекомендуемые ограничения по длине и размер шрифта.

Отступы основаны на индустриальном стандарте US Letter (8.5" x 11"):
- Левое поле страницы: 1.5 дюйма
- Правое поле страницы: 1.0 дюйм
- Dialogue: дополнительные отступы 2.5" слева и 1.5" справа

Источник: PDF-руководство по форматированию из ТЗ, раздел 4.
"""

from app.services.formatting.types import FormattingRule, TextAlignment

# Словарь правил форматирования для каждого типа блока.
# Ключ — строковое значение BlockType, значение — FormattingRule.

FORMATTING_RULES: dict[str, FormattingRule] = {
    "scene_heading": FormattingRule(
        block_type="scene_heading",
        uppercase=True,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=2,
        margin_bottom_lines=1,
        max_characters_per_line=60,
    ),
    "action": FormattingRule(
        block_type="action",
        uppercase=False,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=1,
        margin_bottom_lines=0,
        max_lines=5,
        max_characters_per_line=60,
    ),
    "character_cue": FormattingRule(
        block_type="character_cue",
        uppercase=True,
        alignment=TextAlignment.CENTER,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=1,
        margin_bottom_lines=0,
        max_characters_per_line=35,
    ),
    "parenthetical": FormattingRule(
        block_type="parenthetical",
        uppercase=False,
        alignment=TextAlignment.LEFT,
        indent_left_inches=3.0,
        indent_right_inches=2.0,
        margin_top_lines=0,
        margin_bottom_lines=0,
        max_characters_per_line=25,
    ),
    "dialogue": FormattingRule(
        block_type="dialogue",
        uppercase=False,
        alignment=TextAlignment.LEFT,
        indent_left_inches=2.5,
        indent_right_inches=1.5,
        margin_top_lines=0,
        margin_bottom_lines=0,
        max_lines=10,
        max_characters_per_line=35,
    ),
    "transition": FormattingRule(
        block_type="transition",
        uppercase=True,
        alignment=TextAlignment.RIGHT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=1,
        margin_bottom_lines=0,
        max_characters_per_line=50,
    ),
    "shot": FormattingRule(
        block_type="shot",
        uppercase=True,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=1,
        margin_bottom_lines=0,
        max_characters_per_line=60,
    ),
    "montage": FormattingRule(
        block_type="montage",
        uppercase=True,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=2,
        margin_bottom_lines=0,
        max_characters_per_line=60,
    ),
    "end_montage": FormattingRule(
        block_type="end_montage",
        uppercase=True,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=1,
        margin_bottom_lines=2,
        max_characters_per_line=60,
    ),
    "flashback_start": FormattingRule(
        block_type="flashback_start",
        uppercase=True,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=2,
        margin_bottom_lines=0,
        max_characters_per_line=60,
    ),
    "flashback_end": FormattingRule(
        block_type="flashback_end",
        uppercase=True,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=1,
        margin_bottom_lines=2,
        max_characters_per_line=60,
    ),
    "dream_sequence_start": FormattingRule(
        block_type="dream_sequence_start",
        uppercase=True,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=2,
        margin_bottom_lines=0,
        max_characters_per_line=60,
    ),
    "dream_sequence_end": FormattingRule(
        block_type="dream_sequence_end",
        uppercase=True,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=1,
        margin_bottom_lines=2,
        max_characters_per_line=60,
    ),
    "act_heading": FormattingRule(
        block_type="act_heading",
        uppercase=True,
        alignment=TextAlignment.CENTER,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=2,
        margin_bottom_lines=1,
        max_characters_per_line=60,
    ),
    "end_of_act": FormattingRule(
        block_type="end_of_act",
        uppercase=True,
        alignment=TextAlignment.CENTER,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=1,
        margin_bottom_lines=2,
        max_characters_per_line=60,
    ),
    "note": FormattingRule(
        block_type="note",
        uppercase=False,
        alignment=TextAlignment.LEFT,
        indent_left_inches=0.0,
        indent_right_inches=0.0,
        margin_top_lines=0,
        margin_bottom_lines=0,
        font_size=12,
        bold=False,
    ),
}
