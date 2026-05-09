"""
Схемы для аутентификации.

Определяют структуру запросов и ответов для эндпоинтов
регистрации, входа, обновления токенов и профиля.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Запрос на регистрацию нового пользователя."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Запрос на вход в систему."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Ответ с парой JWT-токенов."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Запрос на обновление access-токена."""

    refresh_token: str


class UserResponse(BaseModel):
    """Публичная информация о пользователе."""

    id: uuid.UUID
    email: str
    display_name: str
    created_at: datetime


class UserUpdateRequest(BaseModel):
    """Запрос на обновление профиля."""

    display_name: str | None = Field(default=None, min_length=1, max_length=255)
