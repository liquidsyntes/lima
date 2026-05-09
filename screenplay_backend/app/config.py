"""
Конфигурация приложения.

Загружает настройки из переменных окружения и файла .env.
Все секретные значения (пароли, ключи) хранятся только в переменных окружения.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения."""

    # --- База данных ---
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/screenplay"
    DATABASE_ECHO: bool = False

    # --- JWT ---
    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Экспорт ---
    EXPORT_STORAGE_PATH: str = "./storage/exports"
    PDF_PAGE_SIZE: str = "letter"

    # --- Режим отладки ---
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
