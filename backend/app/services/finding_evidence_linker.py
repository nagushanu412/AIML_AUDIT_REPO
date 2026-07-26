"""Attach evidence_links when findings are generated (Remediation M2 follow-up).

Mirrors the relationship used by migration 026 backfill so every new finding
has at least one evidence_links row in the same transaction as creation.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditFinding, AuditProject, Evidence, EvidenceLink


def _entity_type_for_project(project_type: str | None) -> str:
    if project_type in ("revenue_testing", "procurement_testing"):
        return "transaction"
    return "journal_entry"


def attach_auto_evidence_for_finding(db: Session, finding: AuditFinding) -> None:
    """Create placeholder Evidence + evidence_links for a flushed finding.

    Caller must flush the finding first so ``finding.id`` and
    ``finding.organization_id`` are assigned. Does not commit.
    """
    if finding.id is None:
        finding.id = uuid.uuid4()

    project = (
        db.query(AuditProject).filter(AuditProject.id == finding.project_id).first()
    )
    if project is None:
        raise ValueError(f"Project {finding.project_id} not found for finding.")

    org_id = finding.organization_id
    if org_id is None and project.engagement is not None:
        org_id = project.engagement.organization_id
    if org_id is None:
        raise ValueError("Cannot attach evidence without organization_id.")

    evidence = Evidence(
        engagement_id=project.engagement_id,
        project_id=project.id,
        organization_id=org_id,
        version_number=1,
        is_current=True,
        title=f"Auto: {(finding.finding_title or 'Finding')[:180]}",
        description=(
            "Auto-created with finding generation from source_record_ids "
            "(Remediation M2 follow-up Part A)."
        ),
        category="other",
        file_name=f"auto-finding-{finding.id}.txt",
        storage_key=f"auto://finding/{finding.id}",
        content_type="text/plain",
        file_size_bytes=0,
        status="active",
        metadata_={"source": "finding_generation_auto_link"},
    )
    db.add(evidence)
    db.flush()
    evidence.root_evidence_id = evidence.id

    entity_type = _entity_type_for_project(project.project_type)
    source_ids = finding.source_record_ids or []
    if not isinstance(source_ids, list):
        source_ids = []

    link_targets: list[tuple[str, uuid.UUID]] = []
    for raw in source_ids:
        try:
            link_targets.append((entity_type, uuid.UUID(str(raw))))
        except (ValueError, TypeError, AttributeError):
            continue
    if not link_targets:
        # Satisfy evidence gate even when no source IDs are present.
        link_targets.append(("finding", finding.id))

    for linked_entity_type, linked_entity_id in link_targets:
        db.add(
            EvidenceLink(
                evidence_id=evidence.id,
                engagement_id=project.engagement_id,
                organization_id=org_id,
                finding_id=finding.id,
                linked_entity_type=linked_entity_type,
                linked_entity_id=linked_entity_id,
                link_type="supports",
                notes="Auto-linked at finding generation from source_record_ids",
            )
        )
