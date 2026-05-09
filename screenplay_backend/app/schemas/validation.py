"""
Схемы для валидации сценария.
"""

import uuid

from pydantic import BaseModel


class ValidationWarning(BaseModel):
    """Одно предупреждение валидации."""

    block_id: uuid.UUID
    warning_type: str
    severity: str  # info / warning / error
    message: str
    rule_name: str


class ValidationResponse(BaseModel):
    """Результат проверки сценария."""

    warnings: list[ValidationWarning]
    total_warnings: int
    total_errors: int
