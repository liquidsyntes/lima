"""
Сервис аутентификации.

Реализует бизнес-логику регистрации, входа, обновления токенов
и управления профилем пользователя.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictException, UnauthorizedException
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class AuthService:
    """Сервис аутентификации и управления пользователями."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, request: RegisterRequest) -> TokenResponse:
        """Зарегистрировать нового пользователя.

        Проверяет уникальность email, хеширует пароль через bcrypt,
        создаёт пользователя и возвращает пару JWT-токенов.
        """
        # Проверка: email уже используется?
        existing = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if existing.scalar_one_or_none():
            raise ConflictException(
                "Пользователь с таким email уже зарегистрирован"
            )

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            display_name=request.display_name,
        )
        self.db.add(user)
        await self.db.flush()

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Войти в систему по email и паролю.

        Проверяет учётные данные и возвращает пару JWT-токенов.
        """
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(request.password, user.password_hash):
            raise UnauthorizedException("Неверный email или пароль")

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, request: RefreshRequest) -> TokenResponse:
        """Обновить access-токен по refresh-токену.

        Проверяет, что переданный токен является refresh-токеном
        (а не access), и что пользователь существует.
        """
        try:
            payload = decode_token(request.refresh_token)
        except Exception:
            raise UnauthorizedException("Refresh-токен недействителен или истёк")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Переданный токен не является refresh-токеном")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Некорректный refresh-токен")

        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedException("Пользователь не найден")

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def get_me(self, user: User) -> UserResponse:
        """Получить профиль текущего пользователя."""
        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
        )

    async def update_me(self, user: User, request: UserUpdateRequest) -> UserResponse:
        """Обновить профиль текущего пользователя."""
        if request.display_name is not None:
            user.display_name = request.display_name
        self.db.add(user)
        await self.db.flush()

        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
        )
