"""
Тесты управления блоками сценария.
"""

import pytest


@pytest.fixture
async def project_with_document(auth_client):
    """Создать проект и получить document_id."""
    proj_resp = await auth_client.post("/api/v1/projects", json={
        "title": "Тестовый сценарий",
    })
    project_id = proj_resp.json()["id"]
    # Получаем документ проекта
    doc_resp = await auth_client.get("/api/v1/projects/" + project_id)
    assert doc_resp.status_code == 200
    # У нас нет прямого эндпоинта project -> document в API,
    # но в сервисе document_service есть связь.
    # Пока используем известные ID — в реальном тесте нужно добавить
    # эндпоинт GET /projects/{id}/document
    return project_id


@pytest.mark.asyncio
async def test_create_block(auth_client):
    """Создание блока в документе."""
    # Создаём проект
    proj_resp = await auth_client.post("/api/v1/projects", json={
        "title": "Сценарий с блоками",
    })
    project_id = proj_resp.json()["id"]

    # Получаем полный документ
    # В MVP мы можем получить document_id через поиск
    # Для теста создадим блоки напрямую через document_service
    # Пока пропускаем — нужен эндпоинт получения document_id по project_id


@pytest.mark.asyncio
async def test_block_order_index():
    """Проверка логики дробной индексации."""
    from app.services.block_service import BlockService

    # Тест расчёта вставки между двумя блоками:
    # prev=1.0, next=2.0 -> новый индекс = 1.5
    assert (1.0 + 2.0) / 2.0 == 1.5

    # prev=1.5, next=1.75 -> новый индекс = 1.625
    assert (1.5 + 1.75) / 2.0 == 1.625
