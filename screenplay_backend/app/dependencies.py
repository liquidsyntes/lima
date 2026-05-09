"""
Общие зависимости FastAPI.

Предоставляют внедряемые зависимости для роутеров:
- get_current_user — получение пользователя из JWT токена
- get_db — асинхронная сессия БД
"""

import uuid

from fastapi import Depends
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.exceptions import UnauthorizedException
from app.models.user import User
from app.utils.security import decode_token

# FastAPI использует http_bearer для извлечения токена из заголовка Authorization
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer()


async def get_db() -> AsyncSession:
    """Зависимость: асинхронная сессия базы данных."""
    async for session in get_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Зависимость: получить текущего пользователя по JWT-токену.

    Извлекает токен из заголовка Authorization: Bearer <token>,
    декодирует его, находит пользователя в базе данных.
    Если токен недействителен или пользователь не найден — 401.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Некорректный токен")
    except JWTError:
        raise UnauthorizedException("Токен недействителен или истёк")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedException("Пользователь не найден")

    return user
