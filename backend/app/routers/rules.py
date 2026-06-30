from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_tenant_context
from app.schemas.rules import (
    RuleResultOut,
    RuleResultsListResponse,
    RunRulesResponse,
)
from app.services.project_access import get_owned_project
from app.services.rule_runner import get_rule_results, run_rules_for_project
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
    db: Session = Depends(get_db),
    tenant: Annotated[TenantContext, Depends(get_tenant_context)] = None,
):
    parsed_id = _parse_project_id(project_id)
    get_owned_project(db, parsed_id, tenant)
    try:
        return run_rules_for_project(db, parsed_id)
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
    get_owned_project(db, parsed_id, tenant)
    rows = get_rule_results(
        db,
        parsed_id,
        rule_code=rule_code,
        limit=limit,
        offset=offset,
    )
    return RuleResultsListResponse(
        project_id=parsed_id,
        total_results=len(rows),
        results=[RuleResultOut(**row) for row in rows],
    )
