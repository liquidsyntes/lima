"""
Точка входа FastAPI-приложения.

Настраивает CORS, подключает роутеры API v1, регистрирует
обработчики исключений и события жизненного цикла приложения.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения.

    При старте: инициализация хранилища, подключение к БД.
    При остановке: корректное завершение соединений.
    """
    from app.utils.storage import ensure_storage_dirs
    from app.database import init_db

    ensure_storage_dirs()
    await init_db()
    yield


app = FastAPI(
    title="Screenplay Editor API",
    description="API для онлайн-редактора киносценариев",
    version="0.1.0",
    lifespan=lifespan,
)

# Настройка CORS для доступа фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.api.router import api_router

app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервера."""
    return {"status": "ok"}
