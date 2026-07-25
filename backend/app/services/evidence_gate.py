"""Evidence gate — findings must have linked evidence before risk scoring."""

from __future__ import annotations

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit import AuditFinding, EvidenceLink


class EvidenceGateViolation(Exception):
    """Raised when risk scoring is blocked because a finding lacks evidence."""


def assert_project_findings_have_evidence(db: Session, project_id: uuid.UUID) -> None:
    """Block risk scoring if any finding on the project has zero evidence_links."""
    bare = (
        db.query(AuditFinding.id)
        .outerjoin(EvidenceLink, EvidenceLink.finding_id == AuditFinding.id)
        .filter(AuditFinding.project_id == project_id)
        .group_by(AuditFinding.id)
        .having(func.count(EvidenceLink.id) == 0)
        .all()
    )
    if not bare:
        return
    finding_id = bare[0][0]
    raise EvidenceGateViolation(
        f"Finding {finding_id} has no linked evidence; cannot score risk."
    )
