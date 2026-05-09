"""
Движок форматирования сценария.

Предоставляет правила форматирования для каждого типа блока.
Не применяет визуальное форматирование самостоятельно — вместо этого
возвращает метаданные, которые фронтенд и экспортёр используют
для корректного отображения блоков.

Также содержит логику контекстных переходов: какой тип блока
должен следовать после текущего при нажатии Enter.
"""

from app.services.formatting.types import FormattingRule
from app.services.formatting.rules import FORMATTING_RULES


class FormattingEngine:
    """Движок форматирования сценарных блоков.

    Предоставляет:
    - Правила форматирования для каждого типа блока
    - Рекомендуемый следующий тип блока при нажатии Enter
    - Рекомендуемый тип блока при нажатии Tab (циклический перебор)
    """

    # Порядок циклического перебора типов блоков при нажатии Tab
    TAB_CYCLE_ORDER: list[str] = [
        "scene_heading",
        "action",
        "character_cue",
        "parenthetical",
        "dialogue",
        "transition",
    ]

    # Рекомендуемый следующий тип блока при нажатии Enter.
    # Зависит от текущего типа блока.
    ENTER_TRANSITIONS: dict[str, str] = {
        "scene_heading": "action",
        "action": "action",
        "character_cue": "dialogue",
        "parenthetical": "dialogue",
        "dialogue": "action",
        "transition": "scene_heading",
        "shot": "action",
        "montage": "action",
        "end_montage": "action",
        "flashback_start": "action",
        "flashback_end": "action",
        "dream_sequence_start": "action",
        "dream_sequence_end": "action",
        "act_heading": "scene_heading",
        "end_of_act": "action",
        "note": "action",
    }

    @classmethod
    def get_formatting(cls, block_type: str) -> FormattingRule:
        """Получить правило форматирования для типа блока.

        Если тип не найден, возвращает правило по умолчанию (как action).
        """
        return FORMATTING_RULES.get(
            block_type,
            FormattingRule(
                block_type=block_type,
                alignment="left",
                font_size=12,
            ),
        )

    @classmethod
    def get_all_formatting_rules(cls) -> dict[str, FormattingRule]:
        """Получить словарь всех правил форматирования."""
        return dict(FORMATTING_RULES)

    @classmethod
    def get_next_block_type(cls, current_type: str) -> str:
        """Получить рекомендуемый тип блока после нажатия Enter.

        Реализует сценарный флоу из раздела 7.5 ТЗ:
        - Enter после Scene Heading → Action
        - Enter после Character Cue → Dialogue
        - Enter после Dialogue → Action или Character Cue (по контексту, здесь Action)
        - Enter после Parenthetical → Dialogue
        """
        return cls.ENTER_TRANSITIONS.get(current_type, "action")

    @classmethod
    def get_tab_next_type(cls, current_type: str) -> str:
        """Получить следующий тип блока при нажатии Tab (циклически).

        Реализует циклическое переключение из раздела 7.5 ТЗ:
        Tab / Shift+Tab переключает тип блока по кругу.
        """
        cycle = cls.TAB_CYCLE_ORDER
        if current_type in cycle:
            idx = cycle.index(current_type)
            next_idx = (idx + 1) % len(cycle)
            return cycle[next_idx]
        return cycle[0]

    @classmethod
    def get_tab_prev_type(cls, current_type: str) -> str:
        """Получить предыдущий тип блока при нажатии Shift+Tab (циклически)."""
        cycle = cls.TAB_CYCLE_ORDER
        if current_type in cycle:
            idx = cycle.index(current_type)
            prev_idx = (idx - 1) % len(cycle)
            return cycle[prev_idx]
        return cycle[0]
