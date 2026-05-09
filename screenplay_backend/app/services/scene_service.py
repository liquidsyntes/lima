"""
Сервис структурной навигации по сценарию.

Анализирует последовательность блоков и строит дерево документа:
- Список сцен с номерами и slug lines
- Разбивка по актам (для телевизионного формата)
- Статистика: количество сцен, слов, примерный хронометраж
- Номера страниц для каждой сцены (приблизительно)

Используется для левой панели навигации в редакторе (раздел 7.7 ТЗ).
"""

import uuid


def _get_block_type(block) -> str:
    """Получить строковое значение типа блока."""
    if hasattr(block.block_type, "value"):
        return block.block_type.value
    return block.block_type


class SceneService:
    """Сервис извлечения структуры документа."""

    # Коэффициенты для расчёта страниц
    CHARS_PER_LINE = 60  # Символов в строке Courier 12pt
    LINES_PER_PAGE = 45  # Строк на странице US Letter
    PAGE_MINUTES_RATIO = 1.0  # 1 страница = ~1 минута

    @classmethod
    def extract_structure(cls, blocks: list) -> dict:
        """Извлечь полную структуру документа.

        Возвращает:
        - scenes: список сцен с информацией о каждой
        - acts: список актов (для TV-формата)
        - statistics: общая статистика документа
        """
        scenes = cls._extract_scenes(blocks)
        acts = cls._extract_acts(blocks)
        statistics = cls._get_statistics(blocks, scenes)

        return {
            "scenes": scenes,
            "acts": acts,
            "statistics": statistics,
        }

    @classmethod
    def _extract_scenes(cls, blocks: list) -> list[dict]:
        """Извлечь список сцен из последовательности блоков.

        Сцена начинается с scene_heading (slug line) и заканчивается
        перед следующим scene_heading или в конце документа.
        """
        scenes = []
        current_scene = None
        scene_number = 0
        scene_start_idx = 0

        for i, block in enumerate(blocks):
            block_type = _get_block_type(block)

            if block_type == "scene_heading":
                # Закрываем предыдущую сцену
                if current_scene is not None:
                    current_scene["block_count"] = i - scene_start_idx
                    current_scene["end_block_id"] = blocks[i - 1].id if i > 0 else block.id
                    scenes.append(current_scene)

                scene_number += 1
                current_scene = {
                    "scene_number": scene_number,
                    "slug_line": block.text_content or "",
                    "block_id": str(block.id),
                    "order_index": block.order_index,
                    "start_block_id": str(block.id),
                    "act_name": None,
                    "estimated_pages": 0.0,
                    "estimated_minutes": 0.0,
                }
                scene_start_idx = i

        # Закрываем последнюю сцену
        if current_scene is not None:
            current_scene["block_count"] = len(blocks) - scene_start_idx
            current_scene["end_block_id"] = str(blocks[-1].id) if blocks else None
            scenes.append(current_scene)

        # Назначаем акты сценам
        act_name = None
        for scene in scenes:
            # Ищем акт, к которому относится эта сцена
            for act in cls._extract_acts(blocks):
                if act["order_index"] <= scene["order_index"]:
                    act_name = act["name"]
            scene["act_name"] = act_name

        # Считаем примерный хронометраж для каждой сцены
        for scene in scenes:
            scene_chars = cls._count_scene_characters(blocks, scene)
            estimated_lines = scene_chars / cls.CHARS_PER_LINE
            estimated_pages = estimated_lines / cls.LINES_PER_PAGE
            scene["estimated_pages"] = round(estimated_pages, 1)
            scene["estimated_minutes"] = round(estimated_pages * cls.PAGE_MINUTES_RATIO, 1)

        return scenes

    @classmethod
    def _extract_acts(cls, blocks: list) -> list[dict]:
        """Извлечь список актов (для телевизионного формата).

        Акт начинается с act_heading и заканчивается end_of_act.
        Также поддерживает Teaser (перед Act One) и Tag (в конце).
        """
        acts = []

        for block in blocks:
            block_type = _get_block_type(block)
            if block_type == "act_heading":
                acts.append({
                    "name": block.text_content or "ACT",
                    "block_id": str(block.id),
                    "order_index": block.order_index,
                })

        return acts

    @classmethod
    def _get_statistics(cls, blocks: list, scenes: list[dict]) -> dict:
        """Подсчитать общую статистику документа."""
        total_chars = sum(
            len(block.text_content or "") for block in blocks
            if _get_block_type(block) != "note"
        )
        total_words = sum(
            len((block.text_content or "").split())
            for block in blocks
            if _get_block_type(block) != "note"
        )

        estimated_lines = total_chars / cls.CHARS_PER_LINE
        total_pages = max(1, estimated_lines / cls.LINES_PER_PAGE)
        # Добавляем титульную страницу
        total_pages_with_title = total_pages + 1

        return {
            "scene_count": len(scenes),
            "act_count": len([a for a in cls._extract_acts(blocks)]),
            "block_count": len(blocks),
            "character_count": total_chars,
            "word_count": total_words,
            "estimated_pages": round(total_pages_with_title, 1),
            "estimated_minutes": round(total_pages, 1),
            "page_count": int(total_pages_with_title),
        }

    @classmethod
    def _count_scene_characters(cls, blocks: list, scene: dict) -> int:
        """Подсчитать количество символов в конкретной сцене."""
        start_id = scene.get("start_block_id")
        end_id = scene.get("end_block_id")

        if not start_id:
            return 0

        counting = False
        total = 0

        for block in blocks:
            block_type = _get_block_type(block)
            if block_type == "note":
                continue
            if str(block.id) == start_id:
                counting = True
            if counting:
                total += len(block.text_content or "")
            if str(block.id) == end_id:
                break

        return total
