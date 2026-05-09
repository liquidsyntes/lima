"""
Утилиты безопасности: JWT-токены и хеширование паролей.

JWT используется для аутентификации пользователей через Bearer token.
Пароли хешируются через bcrypt и никогда не хранятся в открытом виде.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Контекст для хеширования паролей (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Захешировать пароль через bcrypt.

    Возвращает хеш, который можно безопасно хранить в базе данных.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить, соответствует ли пароль сохранённому хешу."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str) -> str:
    """Создать JWT access-токен для пользователя.

    Токен содержит идентификатор пользователя и время истечения.
    Время жизни задаётся в настройках ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Создать JWT refresh-токен для обновления access-токена.

    Время жизни задаётся в настройках REFRESH_TOKEN_EXPIRE_DAYS.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Декодировать и проверить JWT-токен.

    Возвращает payload токена.
    Выбрасывает JWTError, если токен недействителен или истёк.
    """
    return jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
