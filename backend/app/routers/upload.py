from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.upload import UploadResponse
from app.services.excel_validator import validate_excel
from app.services.upload_service import resolve_project, save_journal_entries

router = APIRouter(tags=["Upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_journal_entries(
    file: UploadFile = File(...),
    project_id: str | None = Query(
        None,
        description="Optional audit project UUID. Uses default project if omitted.",
    ),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are supported.",
        )

    parsed_project_id: uuid.UUID | None = None
    if project_id:
        try:
            parsed_project_id = uuid.UUID(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID.") from exc

    try:
        project = resolve_project(db, parsed_project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    content = await file.read()
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
