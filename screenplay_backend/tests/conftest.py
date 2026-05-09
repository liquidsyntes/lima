"""
Фикстуры pytest для интеграционных тестов.

Используют SQLite в памяти для тестовой базы данных
и httpx AsyncClient для тестирования API.
"""

import tempfile
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel


def _create_engine():
    """Создать движок с уникальной временной БД для полной изоляции тестов."""
    tmpdir = tempfile.mkdtemp(prefix="screenplay_test_")
    db_path = os.path.join(tmpdir, "test.db")
    return create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)


@pytest_asyncio.fixture
async def db_session():
    """Создать новую БД в памяти для каждого теста — полная изоляция."""
    engine = _create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.close()

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """HTTP-клиент с подменой БД на тестовую сессию."""
    from app.main import app
    from app.dependencies import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client):
    """Зарегистрировать тестового пользователя и вернуть токены."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@screenplay.dev",
        "password": "testpassword123",
        "display_name": "Test User",
    })
    assert response.status_code == 201
    data = response.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


@pytest_asyncio.fixture
async def auth_client(client, registered_user):
    """HTTP-клиент с авторизацией."""
    client.headers["Authorization"] = f"Bearer {registered_user['access_token']}"
    return client
