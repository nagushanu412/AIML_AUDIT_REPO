from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import User
from app.schemas.upload import UploadResponse
from app.services.excel_validator import validate_excel
from app.services.project_access import get_owned_project
from app.services.upload_service import save_journal_entries

router = APIRouter(tags=["Upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_journal_entries(
    file: UploadFile = File(...),
    project_id: str = Query(..., description="Audit project UUID (required)"),
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are supported.",
        )

    try:
        parsed_project_id = uuid.UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID.") from exc

    project = get_owned_project(db, parsed_project_id, current_user)

    settings = get_settings()
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_mb} MB.",
        )

    validation, df = validate_excel(content)

    if not validation.is_valid or df is None:
        return UploadResponse(
            project_id=project.id,
            validation=validation,
            entries_imported=0,
            message="Validation failed. No records were saved.",
        )

    try:
        count = save_journal_entries(db, project, df)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save journal entries: {exc}",
        ) from exc

    return UploadResponse(
        project_id=project.id,
        validation=validation,
        entries_imported=count,
        message=f"Successfully imported {count} journal entries.",
    )
