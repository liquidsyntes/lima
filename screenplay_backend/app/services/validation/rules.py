"""
Правила валидации сценарного форматирования.

Каждое правило — независимый класс, наследующий ValidationRule.
Проверяет соблюдение индустриальных стандартов форматирования
сценариев согласно ТЗ (раздел 7.6 и раздел 12).

Правила разбиты по категориям:
- Формат slug line (scene heading)
- Длина блоков (action, dialogue)
- Позиционирование (parenthetical между cue и dialogue)
- Частота использования (transition)
- Согласованность имён (character cue)
- Специальные проверки (O.S./V.O., camera directions)
"""

import uuid

from app.services.validation.engine import ValidationRule, ValidationContext, ValidationWarning


def _get_block_type(block) -> str:
    """Получить строковое значение типа блока."""
    if hasattr(block.block_type, "value"):
        return block.block_type.value
    return block.block_type


class SlugLineUpperCaseRule(ValidationRule):
    """Проверка: scene heading должен быть в верхнем регистре.

    Slug line (INT./EXT. ...) — один из важнейших элементов формата.
    Заглавные буквы визуально отделяют начало новой сцены.
    """

    rule_name = "slug_not_uppercase"

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "scene_heading":
            return []

        text = block.text_content or ""
        if text != text.upper():
            return [ValidationWarning(
                block_id=block.id,
                warning_type="slug_not_uppercase",
                severity="warning",
                message="Scene heading (slug line) должен быть в верхнем регистре (CAPS)",
                rule_name=self.rule_name,
            )]
        return []


class SlugLineFormatRule(ValidationRule):
    """Проверка: scene heading должен начинаться с INT. / EXT. / INT./EXT.

    Это фундаментальное правило сценарного формата — каждый slug line
    указывает, где происходит сцена: внутри (INT.), снаружи (EXT.)
    или и там и там (INT./EXT.).
    """

    rule_name = "slug_bad_format"

    VALID_PREFIXES = ("INT.", "EXT.", "INT./EXT.", "I./E.")

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "scene_heading":
            return []

        text = (block.text_content or "").strip().upper()
        if not any(text.startswith(p) for p in self.VALID_PREFIXES):
            return [ValidationWarning(
                block_id=block.id,
                warning_type="slug_bad_format",
                severity="warning",
                message=(
                    'Scene heading должен начинаться с INT. / EXT. / INT./EXT. '
                    'с указанием локации и времени суток'
                ),
                rule_name=self.rule_name,
            )]
        return []


class SlugLineTimeOfDayRule(ValidationRule):
    """Проверка: scene heading содержит корректное время суток.

    Допустимые значения: DAY, NIGHT, DAWN, DUSK, LATER, CONTINUOUS, SAME.
    Время суток отделяется от локации дефисом с пробелами: " - DAY".
    """

    rule_name = "slug_bad_time_of_day"

    VALID_TIMES = {"DAY", "NIGHT", "DAWN", "DUSK", "LATER", "CONTINUOUS", "SAME"}

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "scene_heading":
            return []

        text = (block.text_content or "").upper()
        # Проверяем наличие " - TIME" в конце
        if " - " not in text:
            return [ValidationWarning(
                block_id=block.id,
                warning_type="slug_bad_time_of_day",
                severity="info",
                message='Scene heading должен заканчиваться на " - DAY" (или NIGHT/DAWN/DUSK/LATER/CONTINUOUS/SAME)',
                rule_name=self.rule_name,
            )]

        # Извлекаем время суток (часть после последнего " - ")
        time_part = text.rsplit(" - ", 1)[-1].strip()
        if time_part not in self.VALID_TIMES:
            return [ValidationWarning(
                block_id=block.id,
                warning_type="slug_bad_time_of_day",
                severity="info",
                message=f'Некорректное время суток: "{time_part}". Допустимые: {", ".join(sorted(self.VALID_TIMES))}',
                rule_name=self.rule_name,
            )]
        return []


class ActionMaxLengthRule(ValidationRule):
    """Проверка: action-блок не должен быть слишком длинным.

    Индустриальный стандарт рекомендует не более 5 строк для блока
    действия. Длинные блоки трудно читать — их следует разбивать
    на более мелкие абзацы.
    """

    rule_name = "action_too_long"

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "action":
            return []

        text = block.text_content or ""
        # Оцениваем количество строк: ~60 символов = 1 строка в Courier 12pt
        chars_per_line = 60
        estimated_lines = max(1, len(text) / chars_per_line)

        if estimated_lines > 5:
            return [ValidationWarning(
                block_id=block.id,
                warning_type="action_too_long",
                severity="warning",
                message=(
                    f"Action-блок слишком длинный (~{int(estimated_lines)} строк). "
                    "Рекомендуется разбивать на блоки не более 5 строк для читаемости"
                ),
                rule_name=self.rule_name,
            )]
        return []


class DialogueMaxLengthRule(ValidationRule):
    """Проверка: диалог не должен быть слишком длинным.

    Длинные реплики (более 10 строк) могут указывать на монолог
    или избыточный текст. В профессиональном режиме выводится
    предупреждение для контроля темпа сцены.
    """

    rule_name = "dialogue_too_long"

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "dialogue":
            return []

        text = block.text_content or ""
        chars_per_line = 35  # Диалог уже чем action
        estimated_lines = max(1, len(text) / chars_per_line)

        if estimated_lines > 10:
            return [ValidationWarning(
                block_id=block.id,
                warning_type="dialogue_too_long",
                severity="warning",
                message=(
                    f"Реплика слишком длинная (~{int(estimated_lines)} строк). "
                    "Рекомендуется не более 10 строк для диалога"
                ),
                rule_name=self.rule_name,
            )]
        return []


class ParentheticalPositionRule(ValidationRule):
    """Проверка: parenthetical должен быть между character cue и dialogue.

    Ремарка (parenthetical) располагается строго между именем персонажа
    и его репликой. Если она стоит в другом месте — это ошибка
    структуры документа.
    """

    rule_name = "parenthetical_bad_position"

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "parenthetical":
            return []

        prev_block, _, next_block = context.get_adjacent_blocks(index)

        # Перед parenthetical должен быть character_cue
        prev_ok = prev_block is not None and _get_block_type(prev_block) == "character_cue"
        # После parenthetical должен быть dialogue
        next_ok = next_block is not None and _get_block_type(next_block) == "dialogue"

        if not prev_ok or not next_ok:
            return [ValidationWarning(
                block_id=block.id,
                warning_type="parenthetical_bad_position",
                severity="error",
                message="Parenthetical (ремарка) должна находиться между character cue и dialogue",
                rule_name=self.rule_name,
            )]
        return []


class TransitionFrequencyRule(ValidationRule):
    """Проверка: transitions не должны использоваться слишком часто.

    В режиме professional: если более 3 transitions на 20 блоков —
    это считается избыточным использованием монтажных переходов.
    """

    rule_name = "transition_too_frequent"

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        if context.mode != "professional":
            return []

        block = context.blocks[index]
        if _get_block_type(block) != "transition":
            return []

        # Считаем transitions в окне из 20 блоков вокруг текущего
        start = max(0, index - 10)
        end = min(len(context.blocks), index + 10)
        window = context.blocks[start:end]
        transition_count = sum(
            1 for b in window if _get_block_type(b) == "transition"
        )

        if transition_count > 3:
            return [ValidationWarning(
                block_id=block.id,
                warning_type="transition_too_frequent",
                severity="info",
                message="Слишком частое использование transitions — рекомендуется не более 3 на страницу",
                rule_name=self.rule_name,
            )]
        return []


class CharacterNameConsistencyRule(ValidationRule):
    """Проверка: имена персонажей должны быть написаны одинаково.

    Сравнивает character cue без учёта суффиксов (V.O., O.S., CONT'D).
    "JOHN" и "JOHN (V.O.)" — один персонаж. "JOHN" и "JOHNNY" —
    разные написания одного имени, возможна опечатка.
    """

    rule_name = "character_name_inconsistent"

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "character_cue":
            return []

        text = (block.text_content or "").strip()
        # Извлекаем базовое имя без суффикса
        base_name = text.upper()
        for suffix in ("(V.O.)", "(O.S.)", "(CONT'D)", "(OC)", "(OS)"):
            base_name = base_name.replace(suffix, "")
        base_name = base_name.strip()

        if not base_name:
            return []

        # Ищем похожие имена во всём документе
        seen_names: dict[str, str] = {}
        warnings = []

        for other in context.blocks:
            if _get_block_type(other) != "character_cue":
                continue
            if other.id == block.id:
                continue

            other_text = (other.text_content or "").strip().upper()
            for suffix in ("(V.O.)", "(O.S.)", "(CONT'D)", "(OC)", "(OS)"):
                other_text = other_text.replace(suffix, "")
            other_text = other_text.strip()

            if not other_text:
                continue

            # Проверяем на возможную опечатку: одно имя длинное, другое короткое
            # и они начинаются одинаково
            if len(base_name) >= 3 and len(other_text) >= 3:
                if base_name[0] == other_text[0] and (
                    base_name.startswith(other_text[:3])
                    or other_text.startswith(base_name[:3])
                ):
                    if base_name != other_text:
                        key = tuple(sorted([base_name, other_text]))
                        if key not in seen_names:
                            seen_names[key] = other_text
                            warnings.append(ValidationWarning(
                                block_id=block.id,
                                warning_type="character_name_inconsistent",
                                severity="warning",
                                message=(
                                    f'Возможно несогласованное имя персонажа: '
                                    f'"{base_name}" и "{other_text}"'
                                ),
                                rule_name=self.rule_name,
                            ))

        return warnings[:5]  # Ограничиваем количество однотипных предупреждений


class OSVOConsistencyRule(ValidationRule):
    """Проверка: корректность использования O.S. и V.O.

    O.S. (Off Screen) — персонаж в сцене, но не в кадре.
    V.O. (Voice Over) — закадровый голос, narration.
    Проверяет, что суффиксы используются осмысленно, без путаницы.
    """

    rule_name = "os_vo_confusion"

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "character_cue":
            return []

        text = (block.text_content or "").upper()

        has_os = "(O.S.)" in text or "(OS)" in text
        has_vo = "(V.O.)" in text or "(VO)" in text

        if has_os and has_vo:
            return [ValidationWarning(
                block_id=block.id,
                warning_type="os_vo_confusion",
                severity="info",
                message="Персонаж использует одновременно O.S. и V.O. — выберите что-то одно",
                rule_name=self.rule_name,
            )]
        return []


class CameraDirectionRule(ValidationRule):
    """Проверка: camera directions в spec-сценарии.

    В spec-скрипте (который пишется на продажу) не рекомендуется
    использовать операторские указания (CLOSE UP, ANGLE ON, PAN TO).
    Эти указания — прерогатива shooting script, а не spec.
    """

    rule_name = "camera_direction_in_spec"

    CAMERA_TERMS = (
        "CLOSE UP", "CLOSE-UP", "CLOSE ON", "ANGLE ON", "ANGLE TO",
        "PAN TO", "PAN LEFT", "PAN RIGHT", "TILT UP", "TILT DOWN",
        "ZOOM IN", "ZOOM OUT", "DOLLY", "TRACKING", "CRANE",
        "WIDE SHOT", "MEDIUM SHOT", "TWO SHOT", "POV SHOT",
        "LOW ANGLE", "HIGH ANGLE", "AERIAL SHOT",
    )

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        if context.mode != "professional":
            return []

        block = context.blocks[index]
        if _get_block_type(block) != "action":
            return []

        text = (block.text_content or "").upper()
        for term in self.CAMERA_TERMS:
            if term in text:
                return [ValidationWarning(
                    block_id=block.id,
                    warning_type="camera_direction_in_spec",
                    severity="info",
                    message=(
                        f'Обнаружена операторская ремарка "{term}". '
                        "В spec-сценарии рекомендуется избегать camera directions"
                    ),
                    rule_name=self.rule_name,
                )]
        return []


class EmptyDialogueRule(ValidationRule):
    """Проверка: диалог не должен быть пустым.

    Character cue без последующего dialogue (или с пустым dialogue) —
    вероятно, ошибка. Исключение: если персонаж молча появляется
    и это описано в action.
    """

    rule_name = "empty_dialogue"

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "dialogue":
            return []

        text = (block.text_content or "").strip()
        if not text:
            return [ValidationWarning(
                block_id=block.id,
                warning_type="empty_dialogue",
                severity="warning",
                message="Пустая реплика диалога",
                rule_name=self.rule_name,
            )]
        return []


class ConsecutiveParentheticalRule(ValidationRule):
    """Проверка: не более двух parenthetical подряд.

    Избыточное использование ремарок между именем персонажа и диалогом
    делает текст трудночитаемым. Рекомендуется не более 1-2 ремарок.
    """

    rule_name = "too_many_parentheticals"

    def validate(self, index: int, context: ValidationContext) -> list[ValidationWarning]:
        block = context.blocks[index]
        if _get_block_type(block) != "parenthetical":
            return []

        # Считаем подряд идущие parenthetical
        count = 1
        # Проверяем следующий блок
        if index + 1 < len(context.blocks):
            next_block = context.blocks[index + 1]
            if _get_block_type(next_block) == "parenthetical":
                count += 1

        if count > 1 and self._count_consecutive(context, index) >= 2:
            return [ValidationWarning(
                block_id=block.id,
                warning_type="too_many_parentheticals",
                severity="warning",
                message="Слишком много ремарок (parenthetical) подряд — рекомендуется не более 1-2",
                rule_name=self.rule_name,
            )]
        return []

    def _count_consecutive(self, context: ValidationContext, start: int) -> int:
        """Подсчитать количество последовательных parenthetical."""
        count = 0
        for i in range(start, len(context.blocks)):
            if _get_block_type(context.blocks[i]) == "parenthetical":
                count += 1
            else:
                break
        return count
