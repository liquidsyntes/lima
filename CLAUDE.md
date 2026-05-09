# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Онлайн-сервис для написания киносценариев в браузере — a web-based SaaS screenplay editor. Backend на Python, frontend SPA в браузере. Полное техническое задание в `tz.md`.

## Tech stack (from TZ)

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy/SQLModel, PostgreSQL, Alembic, Pydantic
- **Frontend:** React/Next.js или Vue/Nuxt, ProseMirror/TipTap/Lexical для редактора
- **Export:** PDF (серверная генерация), Fountain, TXT
- **Optional:** Celery/RQ + Redis для фоновых задач

## Critical requirement: Russian comments

**Все комментарии в коде должны быть на русском языке.** Docstrings, inline-комментарии, пояснения бизнес-логики — всё по-русски. Комментарии на английском недопустимы. Подробные требования к комментированию: `tz.md` раздел 15 (строка 442).

## Architecture (from TZ)

### Data model
Core entities: `User` → `Project` → `ScriptDocument` → `ScriptBlock`. Each block has a `block_type` (scene_heading, action, character_cue, parenthetical, dialogue, transition, etc.), `order_index`, `text_content`, and `meta_json`. Separate `Revision`, `ExportJob`, and `Comment` entities.

### Screenplay block types
The editor is NOT a rich-text editor — it's a structured document editor. Every paragraph is a typed block with automatic formatting rules:

| Block type | Formatting |
|---|---|
| Scene Heading (slug line) | UPPERCASE, `INT./EXT. LOCATION - TIME` |
| Action | Left-aligned, present tense |
| Character Cue | Centered, UPPERCASE, supports `(V.O.)`, `(O.S.)`, `(CONT'D)` |
| Parenthetical | Narrow block between cue and dialogue |
| Dialogue | Narrow text block under character |
| Transition | UPPERCASE, right-aligned |
| Act Heading / End of Act | TV format support |
| Flashback / Dream Sequence | Start/end markers |

### Editor behavior
- `Enter` key transitions between block types contextually (e.g., after Scene Heading → Action, after Character Cue → Dialogue)
- `Tab` / `Shift+Tab` cycles block types
- Autosave every N seconds with revision history
- Three modes: Draft, Professional, Read/Preview

### MVP scope (раздел 17, строка 477)
Auth → projects CRUD → structured screenplay editor with block types → auto-formatting → hotkeys → basic validation → title page → scene navigator → autosave → PDF + Fountain export → light/dark UI.

## Commands

```bash
# Установка зависимостей
cd screenplay_backend
pip install -r requirements.txt

# Запуск сервера для разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Swagger UI
# http://localhost:8000/docs

# Запуск тестов
pytest tests/ -v

# Миграции Alembic (после настройки alembic.ini)
alembic upgrade head
alembic revision --autogenerate -m "описание_изменения"
```

## Environment

The script `start-claude-deepseek.ps1` configures Claude Code to use DeepSeek's API as the model backend. It sets `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, and model environment variables, then launches `claude` in this directory.
