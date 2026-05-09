"""
Асинхронное подключение к PostgreSQL.

Использует asyncpg через SQLAlchemy для асинхронной работы с базой данных.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from app.config import settings

# Асинхронный движок SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
)

# Фабрика сессий для внедрения зависимостей
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Создать все таблицы в базе данных (только для разработки).

    В production следует использовать Alembic миграции.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    """Зависимость FastAPI: предоставляет сессию базы данных.

    Сессия автоматически закрывается после завершения запроса.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
