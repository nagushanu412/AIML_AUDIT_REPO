from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import RuleMaster, User
from app.schemas.rules_master import RuleMasterOut, RuleMasterUpdate, validate_rule_config
from app.services.rule_config import get_default_config

router = APIRouter(prefix="/rules", tags=["Rules Master"])


def _get_rule_or_404(db: Session, rule_id: UUID) -> RuleMaster:
    rule = db.query(RuleMaster).filter(RuleMaster.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.get("", response_model=list[RuleMasterOut])
def list_rules(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    del current_user
    return db.query(RuleMaster).order_by(RuleMaster.rule_code).all()


@router.get("/{rule_id}", response_model=RuleMasterOut)
def get_rule(
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    del current_user
    return _get_rule_or_404(db, rule_id)


@router.patch("/{rule_id}", response_model=RuleMasterOut)
def update_rule(
    rule_id: UUID,
    body: RuleMasterUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_auditor)] = None,
):
    del current_user
    rule = _get_rule_or_404(db, rule_id)
    updates = body.model_dump(exclude_unset=True)

    if "config_schema" in updates and updates["config_schema"] is not None:
        try:
            validated = validate_rule_config(rule.rule_code, updates["config_schema"])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        current = dict(rule.config_schema or get_default_config(rule.rule_code))
        current.update(validated)
        updates["config_schema"] = current

    for field, value in updates.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule
