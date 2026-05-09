"""
Тесты движка валидации.
"""

import uuid

from app.services.validation.engine import ValidationEngine, ValidationContext
from app.services.validation.rules import (
    SlugLineUpperCaseRule,
    SlugLineFormatRule,
    SlugLineTimeOfDayRule,
    ActionMaxLengthRule,
    DialogueMaxLengthRule,
    ParentheticalPositionRule,
    EmptyDialogueRule,
    ConsecutiveParentheticalRule,
)
from app.models.block import ScriptBlock, BlockType


def make_block(block_type: BlockType, text: str, order: float = 0.0):
    """Создать тестовый блок сценария."""
    return ScriptBlock(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        order_index=order,
        block_type=block_type,
        text_content=text,
        meta_json={},
        scene_number=None,
    )


class TestSlugLineRules:
    """Проверка правил slug line."""

    def test_valid_slug(self):
        """Корректный slug line не вызывает предупреждений."""
        block = make_block(BlockType.SCENE_HEADING, "INT. COFFEE SHOP - DAY", 1.0)
        context = ValidationContext(blocks=[block])
        rule = SlugLineUpperCaseRule()
        warnings = rule.validate(0, context)
        assert len(warnings) == 0

    def test_slug_not_uppercase(self):
        """Slug line в нижнем регистре — предупреждение."""
        block = make_block(BlockType.SCENE_HEADING, "int. coffee shop - day", 1.0)
        context = ValidationContext(blocks=[block])
        rule = SlugLineUpperCaseRule()
        warnings = rule.validate(0, context)
        assert len(warnings) == 1
        assert warnings[0].warning_type == "slug_not_uppercase"

    def test_slug_bad_format(self):
        """Slug line без INT./EXT. — предупреждение."""
        block = make_block(BlockType.SCENE_HEADING, "COFFEE SHOP - DAY", 1.0)
        context = ValidationContext(blocks=[block])
        rule = SlugLineFormatRule()
        warnings = rule.validate(0, context)
        assert len(warnings) == 1
        assert warnings[0].warning_type == "slug_bad_format"

    def test_slug_good_time_of_day(self):
        """Корректное время суток — без предупреждений."""
        block = make_block(BlockType.SCENE_HEADING, "INT. HOUSE - NIGHT", 1.0)
        context = ValidationContext(blocks=[block])
        rule = SlugLineTimeOfDayRule()
        warnings = rule.validate(0, context)
        assert len(warnings) == 0

    def test_slug_bad_time_of_day(self):
        """Некорректное время суток — предупреждение."""
        block = make_block(BlockType.SCENE_HEADING, "INT. HOUSE - MORNING", 1.0)
        context = ValidationContext(blocks=[block])
        rule = SlugLineTimeOfDayRule()
        warnings = rule.validate(0, context)
        assert len(warnings) == 1
        assert warnings[0].warning_type == "slug_bad_time_of_day"


class TestBlockLengthRules:
    """Проверка правил длины блоков."""

    def test_action_short_enough(self):
        """Короткий action-блок — без предупреждений."""
        block = make_block(BlockType.ACTION, "Краткое описание.", 1.0)
        context = ValidationContext(blocks=[block])
        rule = ActionMaxLengthRule()
        warnings = rule.validate(0, context)
        assert len(warnings) == 0

    def test_action_too_long(self):
        """Слишком длинный action-блок — предупреждение."""
        long_text = "X " * 200  # ~400 символов = ~7 строк
        block = make_block(BlockType.ACTION, long_text, 1.0)
        context = ValidationContext(blocks=[block])
        rule = ActionMaxLengthRule()
        warnings = rule.validate(0, context)
        assert len(warnings) == 1
        assert warnings[0].warning_type == "action_too_long"


class TestPositionRules:
    """Проверка правил позиционирования блоков."""

    def test_parenthetical_correct_position(self):
        """Parenthetical между character_cue и dialogue — без ошибок."""
        blocks = [
            make_block(BlockType.CHARACTER_CUE, "JOHN", 1.0),
            make_block(BlockType.PARENTHETICAL, "whispering", 2.0),
            make_block(BlockType.DIALOGUE, "Hello there.", 3.0),
        ]
        context = ValidationContext(blocks=blocks)
        rule = ParentheticalPositionRule()
        warnings = rule.validate(1, context)
        assert len(warnings) == 0

    def test_parenthetical_bad_position(self):
        """Parenthetical не между cue и dialogue — ошибка."""
        blocks = [
            make_block(BlockType.ACTION, "Something happens.", 1.0),
            make_block(BlockType.PARENTHETICAL, "whispering", 2.0),
            make_block(BlockType.ACTION, "More action.", 3.0),
        ]
        context = ValidationContext(blocks=blocks)
        rule = ParentheticalPositionRule()
        warnings = rule.validate(1, context)
        assert len(warnings) == 1
        assert warnings[0].severity == "error"

    def test_empty_dialogue(self):
        """Пустой диалог — предупреждение."""
        block = make_block(BlockType.DIALOGUE, "", 1.0)
        context = ValidationContext(blocks=[block])
        rule = EmptyDialogueRule()
        warnings = rule.validate(0, context)
        assert len(warnings) == 1
        assert warnings[0].warning_type == "empty_dialogue"


class TestValidationEngine:
    """Интеграционные тесты движка валидации."""

    def test_full_validation(self):
        """Полная валидация сценария с несколькими ошибками."""
        blocks = [
            make_block(BlockType.SCENE_HEADING, "int. bad slug - morning", 1.0),
            make_block(BlockType.ACTION, "X " * 300, 2.0),
            make_block(BlockType.CHARACTER_CUE, "JOHN", 3.0),
            make_block(BlockType.PARENTHETICAL, "smiling", 4.0),
            make_block(BlockType.DIALOGUE, "", 5.0),
            make_block(BlockType.TRANSITION, "CUT TO:", 6.0),
        ]
        engine = ValidationEngine()
        result = engine.validate(blocks, mode="professional")

        assert "warnings" in result
        assert "total_warnings" in result
        assert result["total_warnings"] > 0

        warning_types = {w["warning_type"] for w in result["warnings"]}
        # Должны быть найдены: slug не в uppercase, плохой time of day,
        # длинный action, пустой dialogue
        assert "slug_not_uppercase" in warning_types
        assert "slug_bad_time_of_day" in warning_types
        assert "action_too_long" in warning_types
        assert "empty_dialogue" in warning_types
