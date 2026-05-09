"""
Движок валидации сценария.

Запускает цепочку правил проверки форматирования и возвращает
список предупреждений. Каждое правило — независимый класс,
реализующий единый интерфейс ValidationRule.

Поддерживает два режима:
- draft: мягкая проверка, только критические ошибки
- professional: строгая проверка, все предупреждения
"""

from dataclasses import dataclass, field
import uuid

from pydantic import BaseModel


class ValidationWarning(BaseModel):
    """Одно предупреждение валидации.

    Содержит ссылку на блок, тип предупреждения и человекочитаемое
    описание проблемы на русском языке.
    """

    block_id: uuid.UUID | None = None
    warning_type: str = ""
    severity: str = "info"  # info / warning / error
    message: str = ""
    rule_name: str = ""


@dataclass
class ValidationContext:
    """Контекст выполнения валидации.

    Содержит все блоки документа, индексированные для быстрого
    доступа, и настройки режима проверки.
    """

    blocks: list = field(default_factory=list)
    mode: str = "draft"  # draft / professional

    @property
    def block_count(self) -> int:
        return len(self.blocks)

    def get_adjacent_blocks(self, index: int) -> tuple:
        """Получить соседние блоки (предыдущий, текущий, следующий)."""
        prev_block = self.blocks[index - 1] if index > 0 else None
        current = self.blocks[index]
        next_block = self.blocks[index + 1] if index < len(self.blocks) - 1 else None
        return prev_block, current, next_block


class ValidationRule:
    """Базовый класс правила валидации.

    Все правила наследуются от этого класса и реализуют метод
    validate, который возвращает список предупреждений для
    переданного блока с учётом контекста всего документа.
    """

    rule_name: str = "base_rule"

    def validate(
        self, index: int, context: ValidationContext
    ) -> list[ValidationWarning]:
        """Проверить блок по индексу и вернуть список предупреждений."""
        return []


class ValidationEngine:
    """Движок валидации сценария.

    Запускает все правила проверки на каждом блоке документа
    и собирает предупреждения. Правила зарегистрированы в
    словаре RULES и активируются в зависимости от режима.
    """

    def __init__(self, rules: list[ValidationRule] | None = None):
        self.rules = rules or self._default_rules()

    def _default_rules(self) -> list[ValidationRule]:
        """Список правил валидации по умолчанию."""
        from app.services.validation.rules import (
            SlugLineUpperCaseRule,
            SlugLineFormatRule,
            SlugLineTimeOfDayRule,
            ActionMaxLengthRule,
            DialogueMaxLengthRule,
            ParentheticalPositionRule,
            TransitionFrequencyRule,
            CharacterNameConsistencyRule,
            OSVOConsistencyRule,
            CameraDirectionRule,
            EmptyDialogueRule,
            ConsecutiveParentheticalRule,
        )
        return [
            SlugLineUpperCaseRule(),
            SlugLineFormatRule(),
            SlugLineTimeOfDayRule(),
            ActionMaxLengthRule(),
            DialogueMaxLengthRule(),
            ParentheticalPositionRule(),
            TransitionFrequencyRule(),
            CharacterNameConsistencyRule(),
            OSVOConsistencyRule(),
            CameraDirectionRule(),
            EmptyDialogueRule(),
            ConsecutiveParentheticalRule(),
        ]

    def validate(
        self, blocks: list, mode: str = "draft"
    ) -> dict:
        """Запустить полную валидацию документа.

        Применяет все правила к каждому блоку и собирает предупреждения.
        Возвращает словарь с массивом предупреждений и сводной статистикой.

        Args:
            blocks: список ScriptBlock в порядке следования
            mode: режим проверки (draft/professional)

        Returns:
            dict с ключами: warnings, total_warnings, total_errors
        """
        context = ValidationContext(blocks=blocks, mode=mode)
        all_warnings: list[ValidationWarning] = []

        for i in range(len(blocks)):
            for rule in self.rules:
                try:
                    rule_warnings = rule.validate(i, context)
                    all_warnings.extend(rule_warnings)
                except Exception:
                    # Игнорируем ошибки в отдельных правилах —
                    # одно сломанное правило не должно ломать всю проверку
                    pass

        # Считаем статистику
        total_errors = sum(
            1 for w in all_warnings if w.severity == "error"
        )

        return {
            "warnings": [
                {
                    "block_id": w.block_id,
                    "warning_type": w.warning_type,
                    "severity": w.severity,
                    "message": w.message,
                    "rule_name": w.rule_name,
                }
                for w in all_warnings
            ],
            "total_warnings": len(all_warnings),
            "total_errors": total_errors,
        }
