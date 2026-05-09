"""
Тесты управления проектами.
"""

import pytest


@pytest.mark.asyncio
async def test_create_project(auth_client):
    """Создание нового проекта."""
    response = await auth_client.post("/api/v1/projects", json={
        "title": "Мой первый сценарий",
        "format_type": "feature_film",
        "language": "ru",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Мой первый сценарий"
    assert data["format_type"] == "feature_film"
    assert data["language"] == "ru"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(auth_client):
    """Список проектов пользователя."""
    # Создаём несколько проектов
    for i in range(3):
        await auth_client.post("/api/v1/projects", json={
            "title": f"Сценарий {i}",
            "format_type": "feature_film",
        })

    response = await auth_client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_get_project(auth_client):
    """Получение проекта по ID."""
    # Создаём проект
    create_resp = await auth_client.post("/api/v1/projects", json={
        "title": "Тестовый проект",
    })
    project_id = create_resp.json()["id"]

    response = await auth_client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Тестовый проект"


@pytest.mark.asyncio
async def test_update_project(auth_client):
    """Обновление названия проекта."""
    create_resp = await auth_client.post("/api/v1/projects", json={
        "title": "Черновик",
    })
    project_id = create_resp.json()["id"]

    response = await auth_client.patch(f"/api/v1/projects/{project_id}", json={
        "title": "Финальная версия",
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Финальная версия"


@pytest.mark.asyncio
async def test_delete_project(auth_client):
    """Мягкое удаление проекта."""
    create_resp = await auth_client.post("/api/v1/projects", json={
        "title": "На удаление",
    })
    project_id = create_resp.json()["id"]

    response = await auth_client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_duplicate_project(auth_client):
    """Дублирование проекта."""
    create_resp = await auth_client.post("/api/v1/projects", json={
        "title": "Оригинал",
    })
    project_id = create_resp.json()["id"]

    response = await auth_client.post(f"/api/v1/projects/{project_id}/duplicate")
    assert response.status_code == 201
    data = response.json()
    assert "копия" in data["title"].lower()
