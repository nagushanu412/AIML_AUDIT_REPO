"""Remediation Milestone 2 Step 2 — evidence gate before risk scoring."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from app.database import SessionLocal, validate_database_connection
from app.models.audit import (
    AuditFinding,
    AuditProject,
    ProcurementRiskScore,
    RevenueRiskScore,
    RiskScore,
)
from app.services.evidence_gate import EvidenceGateViolation
from app.services.module_framework.engines import RiskEngineService
from app.services.module_framework.registry import get_module_registry

MODULE_CASES = (
    ("JOURNAL_ENTRY_TESTING", "journal_testing", RiskScore),
    ("REVENUE_TESTING", "revenue_testing", RevenueRiskScore),
    ("PROCUREMENT_TESTING", "procurement_testing", ProcurementRiskScore),
)


def _db_available() -> bool:
    try:
        validate_database_connection()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not available")


def _project_for_type(db: Session, project_type: str) -> AuditProject | None:
    existing = (
        db.query(AuditProject)
        .filter(AuditProject.project_type == project_type)
        .order_by(AuditProject.created_at.desc())
        .first()
    )
    if existing is not None:
        return existing

    # Ensure all three modules can be tested even if only journal projects exist
    donor = (
        db.query(AuditProject)
        .order_by(AuditProject.created_at.desc())
        .first()
    )
    if donor is None:
        return None
    created = AuditProject(
        engagement_id=donor.engagement_id,
        name=f"Evidence Gate {project_type}",
        project_type=project_type,
        status="active",
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return created


def _score_count(db: Session, model, project_id: uuid.UUID) -> int:
    return int(
        db.query(model).filter(model.project_id == project_id).count()
    )


@requires_db
@pytest.mark.parametrize("module_code,project_type,score_model", MODULE_CASES)
def test_risk_scoring_blocked_when_finding_has_no_evidence(
    module_code: str, project_type: str, score_model
):
    """All three modules: bare finding → EvidenceGateViolation, no new risk scores."""
    db = SessionLocal()
    finding_id: uuid.UUID | None = None
    try:
        project = _project_for_type(db, project_type)
        if project is None:
            pytest.skip(f"No {project_type} project available")

        org_id = project.engagement.organization_id if project.engagement else None
        if org_id is None:
            from app.models.audit import AuditEngagement

            eng = (
                db.query(AuditEngagement)
                .filter(AuditEngagement.id == project.engagement_id)
                .first()
            )
            org_id = eng.organization_id if eng else None
        if org_id is None:
            pytest.skip("Project engagement missing organization_id")

        before = _score_count(db, score_model, project.id)

        finding = AuditFinding(
            project_id=project.id,
            organization_id=org_id,
            rule_code="EVIDENCE_GATE_TEST",
            finding_title="Bare finding without evidence",
            observation="Remediation M2 evidence gate test",
            risk_level="high",
            impact="Test",
            recommendation="Link evidence",
            affected_count=1,
            source_record_ids=[],
            status="open",
        )
        db.add(finding)
        db.commit()
        db.refresh(finding)
        finding_id = finding.id

        provider = get_module_registry().resolve_provider(db, module_code)
        engine = RiskEngineService()

        with pytest.raises(EvidenceGateViolation, match="no linked evidence"):
            engine.run(db, project.id, provider)

        db.expire_all()
        after = _score_count(db, score_model, project.id)
        assert after == before, (
            f"{module_code}: risk scores changed despite EvidenceGateViolation "
            f"(before={before}, after={after})"
        )
    finally:
        if finding_id is not None:
            row = db.query(AuditFinding).filter(AuditFinding.id == finding_id).first()
            if row is not None:
                db.delete(row)
                db.commit()
        db.close()


@requires_db
def test_risk_scoring_allowed_when_project_has_no_findings():
    """Gate is finding-centric: projects with zero findings may still run risk."""
    db = SessionLocal()
    try:
        # Prefer a project that currently has no findings
        project = (
            db.query(AuditProject)
            .outerjoin(AuditFinding, AuditFinding.project_id == AuditProject.id)
            .filter(
                AuditProject.project_type == "journal_testing",
                AuditFinding.id.is_(None),
            )
            .first()
        )
        if project is None:
            pytest.skip("No journal project without findings available")

        provider = get_module_registry().resolve_provider(db, "JOURNAL_ENTRY_TESTING")
        # Should not raise EvidenceGateViolation (may still fail for other reasons)
        try:
            RiskEngineService().run(db, project.id, provider)
        except EvidenceGateViolation:
            pytest.fail("EvidenceGateViolation raised with zero findings on project")
        except Exception:
            # Upload/lock/data issues are out of scope for this gate test
            pass
    finally:
        db.close()
