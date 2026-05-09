"""
Тесты аутентификации.
"""

import pytest


@pytest.mark.asyncio
async def test_register(client):
    """Регистрация нового пользователя."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "new@screenplay.dev",
        "password": "securepass123",
        "display_name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Повторная регистрация с тем же email — ошибка."""
    email_data = {
        "email": "dup@screenplay.dev",
        "password": "securepass123",
        "display_name": "Dup User",
    }
    # Первая регистрация
    await client.post("/api/v1/auth/register", json=email_data)
    # Повторная
    response = await client.post("/api/v1/auth/register", json=email_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client, registered_user):
    """Вход зарегистрированного пользователя."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@screenplay.dev",
        "password": "testpassword123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, registered_user):
    """Вход с неверным паролем — ошибка."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@screenplay.dev",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(auth_client):
    """Получение профиля текущего пользователя."""
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@screenplay.dev"
    assert data["display_name"] == "Test User"


@pytest.mark.asyncio
async def test_update_me(auth_client):
    """Обновление отображаемого имени."""
    response = await auth_client.patch("/api/v1/auth/me", json={
        "display_name": "Updated Name",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"
