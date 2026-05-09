"""
Кастомные HTTP-исключения для приложения.

Позволяют централизованно обрабатывать типовые ошибки
и возвращать структурированные ответы API.
"""

from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """Ресурс не найден (404)."""

    def __init__(self, detail: str = "Ресурс не найден"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenException(HTTPException):
    """Доступ запрещён (403)."""

    def __init__(self, detail: str = "Доступ запрещён"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(HTTPException):
    """Некорректный запрос (400)."""

    def __init__(self, detail: str = "Некорректный запрос"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedException(HTTPException):
    """Неавторизованный доступ (401)."""

    def __init__(self, detail: str = "Требуется аутентификация"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ConflictException(HTTPException):
    """Конфликт данных (409)."""

    def __init__(self, detail: str = "Конфликт данных"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
