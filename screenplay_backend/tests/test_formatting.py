"""
Тесты движка форматирования.
"""

import pytest

from app.services.formatting.engine import FormattingEngine
from app.services.formatting.rules import FORMATTING_RULES
from app.services.formatting.types import TextAlignment


class TestFormattingRules:
    """Проверка наличия правил для всех типов блоков."""

    REQUIRED_TYPES = [
        "scene_heading",
        "action",
        "character_cue",
        "parenthetical",
        "dialogue",
        "transition",
        "shot",
        "montage",
        "end_montage",
        "flashback_start",
        "flashback_end",
        "dream_sequence_start",
        "dream_sequence_end",
        "act_heading",
        "end_of_act",
        "note",
    ]

    def test_all_block_types_have_rules(self):
        """Каждый тип блока имеет правило форматирования."""
        for block_type in self.REQUIRED_TYPES:
            assert block_type in FORMATTING_RULES, (
                f"Тип блока '{block_type}' отсутствует в FORMATTING_RULES"
            )

    def test_slug_line_uppercase(self):
        """Scene heading должен быть в верхнем регистре."""
        rule = FORMATTING_RULES["scene_heading"]
        assert rule.uppercase is True

    def test_dialogue_indents(self):
        """Диалог имеет специфические отступы (2.5" слева, 1.5" справа)."""
        rule = FORMATTING_RULES["dialogue"]
        assert rule.indent_left_inches == 2.5
        assert rule.indent_right_inches == 1.5

    def test_transition_alignment(self):
        """Transition выравнивается вправо."""
        rule = FORMATTING_RULES["transition"]
        assert rule.alignment == TextAlignment.RIGHT


class TestFormattingEngine:
    """Проверка логики движка форматирования."""

    def test_enter_after_scene_heading_goes_to_action(self):
        """Enter после Scene Heading → Action."""
        next_type = FormattingEngine.get_next_block_type("scene_heading")
        assert next_type == "action"

    def test_enter_after_character_cue_goes_to_dialogue(self):
        """Enter после Character Cue → Dialogue."""
        next_type = FormattingEngine.get_next_block_type("character_cue")
        assert next_type == "dialogue"

    def test_enter_after_parenthetical_goes_to_dialogue(self):
        """Enter после Parenthetical → Dialogue."""
        next_type = FormattingEngine.get_next_block_type("parenthetical")
        assert next_type == "dialogue"

    def test_enter_after_dialogue_goes_to_action(self):
        """Enter после Dialogue → Action (по умолчанию)."""
        next_type = FormattingEngine.get_next_block_type("dialogue")
        assert next_type == "action"

    def test_tab_cycle(self):
        """Tab циклически переключает типы блоков."""
        assert FormattingEngine.get_tab_next_type("scene_heading") == "action"
        assert FormattingEngine.get_tab_next_type("action") == "character_cue"
        assert FormattingEngine.get_tab_next_type("character_cue") == "parenthetical"
        assert FormattingEngine.get_tab_next_type("parenthetical") == "dialogue"
        assert FormattingEngine.get_tab_next_type("dialogue") == "transition"
        assert FormattingEngine.get_tab_next_type("transition") == "scene_heading"

    def test_shift_tab_cycle(self):
        """Shift+Tab циклически переключает в обратном порядке."""
        assert FormattingEngine.get_tab_prev_type("action") == "scene_heading"
        assert FormattingEngine.get_tab_prev_type("scene_heading") == "transition"

    def test_get_formatting_returns_default_for_unknown_type(self):
        """Для неизвестного типа возвращается правило по умолчанию."""
        rule = FormattingEngine.get_formatting("nonexistent_type")
        assert rule.alignment == TextAlignment.LEFT
        assert rule.font_size == 12
