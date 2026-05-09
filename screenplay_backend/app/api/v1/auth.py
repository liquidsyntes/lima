"""
Эндпоинты аутентификации API v1.

Предоставляют маршруты для регистрации, входа, обновления токенов
и управления профилем текущего пользователя.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя.

    Создаёт учётную запись и возвращает access + refresh токены.
    """
    service = AuthService(db)
    return await service.register(request)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Вход в систему по email и паролю.

    Возвращает пару JWT-токенов для доступа к API.
    """
    service = AuthService(db)
    return await service.login(request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Обновить access-токен по refresh-токену.

    Refresh-токен должен быть валиден и иметь тип "refresh".
    """
    service = AuthService(db)
    return await service.refresh(request)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить профиль текущего пользователя."""
    service = AuthService(db)
    return await service.get_me(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить профиль текущего пользователя (отображаемое имя)."""
    service = AuthService(db)
    return await service.update_me(current_user, request)
