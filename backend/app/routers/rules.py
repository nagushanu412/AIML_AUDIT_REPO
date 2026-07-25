from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.rules import (
    RuleResultOut,
    RuleResultsListResponse,
    RunRulesResponse,
)
from app.services.module_framework.legacy_adapter import DEPRECATION_HEADERS, MODULE_CODES, legacy_adapter
from app.services.tenant_context import TenantContext

router = APIRouter(tags=["Rule Engine"])


def _parse_project_id(project_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid project_id UUID.") from exc


@router.post("/run-rules", response_model=RunRulesResponse)
def run_rules(
    project_id: str = Query(..., description="Audit project UUID (required)"),
    response: Response = None,
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    for key, value in DEPRECATION_HEADERS.items():
        response.headers[key] = value.replace("{code}", "JOURNAL_ENTRY_TESTING")

    parsed_id = _parse_project_id(project_id)
    try:
        result = legacy_adapter.run_rules(
            db, tenant, MODULE_CODES["journal"], parsed_id
        )
        return RunRulesResponse(**result)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Rule engine failed: {exc}") from exc


@router.get("/rule-results", response_model=RuleResultsListResponse)
def list_rule_results(
    project_id: str = Query(..., description="Audit project UUID (required)"),
    rule_code: str | None = Query(None, description="Filter by rule code"),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    parsed_id = _parse_project_id(project_id)
    rows = legacy_adapter.journal_rule_results(
        db, tenant, parsed_id, rule_code=rule_code, limit=limit, offset=offset
    )
    return RuleResultsListResponse(
        project_id=parsed_id,
        total_results=len(rows),
        results=[RuleResultOut(**row) for row in rows],
    )
