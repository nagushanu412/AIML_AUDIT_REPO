from uuid import UUID

from pydantic import BaseModel, Field


class ValidationErrorItem(BaseModel):
    row: int | None = None
    column: str | None = None
    message: str


class ValidationResult(BaseModel):
    is_valid: bool
    total_rows: int = 0
    total_debit: float = 0
    total_credit: float = 0
    errors: list[ValidationErrorItem] = Field(default_factory=list)
    warnings: list[ValidationErrorItem] = Field(default_factory=list)


class UploadResponse(BaseModel):
    project_id: UUID
    validation: ValidationResult
    entries_imported: int
    message: str
