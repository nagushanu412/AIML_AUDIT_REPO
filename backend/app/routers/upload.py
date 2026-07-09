from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.upload import UploadResponse
from app.services.module_framework.legacy_adapter import DEPRECATION_HEADERS, legacy_adapter
from app.services.tenant_context import TenantContext

router = APIRouter(tags=["Upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_journal_entries(
    file: UploadFile = File(...),
    project_id: str = Query(..., description="Audit project UUID (required)"),
    response: Response = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    for key, value in DEPRECATION_HEADERS.items():
        response.headers[key] = value.replace("{code}", "JOURNAL_ENTRY_TESTING")

    legacy_adapter.validate_xlsx(file.filename)
    try:
        parsed_project_id = uuid.UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID.") from exc

    content = await file.read()
    legacy_adapter.validate_size(content)
    try:
        return legacy_adapter.journal_upload(db, tenant, parsed_project_id, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save journal entries: {exc}",
        ) from exc
