"""Remediation M2 Step 3 — backfill evidence_links for bare findings

Revision ID: 026
Revises: 025
Create Date: 2026-07-25

For each audit_finding without an evidence_links row, create a placeholder
Evidence record and link it using journal_entry_ids source-record IDs.
"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _entity_type_for_project(project_type: str | None) -> str:
    if project_type in ("revenue_testing", "procurement_testing"):
        return "transaction"
    return "journal_entry"


def upgrade() -> None:
    conn = op.get_bind()
    bare = conn.execute(
        sa.text(
            """
            SELECT f.id AS finding_id,
                   f.organization_id,
                   f.journal_entry_ids,
                   f.finding_title,
                   p.id AS project_id,
                   p.engagement_id,
                   p.project_type
            FROM audit_findings f
            JOIN audit_projects p ON p.id = f.project_id
            WHERE NOT EXISTS (
                SELECT 1 FROM evidence_links el WHERE el.finding_id = f.id
            )
            """
        )
    ).mappings().all()

    for row in bare:
        finding_id = row["finding_id"]
        org_id = row["organization_id"]
        engagement_id = row["engagement_id"]
        project_id = row["project_id"]
        title = (row["finding_title"] or "Finding")[:200]
        source_ids = row["journal_entry_ids"] or []
        if not isinstance(source_ids, list):
            source_ids = []

        evidence_id = uuid.uuid4()
        conn.execute(
            sa.text(
                """
                INSERT INTO evidence (
                    id, engagement_id, project_id, organization_id,
                    version_number, is_current, title, description, category,
                    file_name, storage_key, content_type, file_size_bytes,
                    status, metadata
                )
                VALUES (
                    :id, :engagement_id, :project_id, :organization_id,
                    1, TRUE, :title, :description, 'other',
                    :file_name, :storage_key, 'text/plain', 0,
                    'active', CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "id": str(evidence_id),
                "engagement_id": str(engagement_id),
                "project_id": str(project_id),
                "organization_id": str(org_id),
                "title": f"Backfill: {title}",
                "description": (
                    "Auto-created by Remediation M2 Step 3 from finding "
                    "source-record IDs (journal_entry_ids)."
                ),
                "file_name": f"backfill-finding-{finding_id}.txt",
                "storage_key": f"backfill://finding/{finding_id}",
                "metadata": '{"source":"remediation_m2_step3"}',
            },
        )

        entity_type = _entity_type_for_project(row["project_type"])
        link_targets: list[tuple[str, uuid.UUID]] = []
        for raw in source_ids:
            try:
                link_targets.append((entity_type, uuid.UUID(str(raw))))
            except (ValueError, TypeError, AttributeError):
                continue
        if not link_targets:
            # Still satisfy the evidence gate with a finding-scoped link
            link_targets.append(("finding", finding_id if isinstance(finding_id, uuid.UUID) else uuid.UUID(str(finding_id))))

        for linked_entity_type, linked_entity_id in link_targets:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO evidence_links (
                        id, evidence_id, engagement_id, organization_id,
                        finding_id, linked_entity_type, linked_entity_id,
                        link_type, notes
                    )
                    VALUES (
                        :id, :evidence_id, :engagement_id, :organization_id,
                        :finding_id, :linked_entity_type, :linked_entity_id,
                        'supports', :notes
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "evidence_id": str(evidence_id),
                    "engagement_id": str(engagement_id),
                    "organization_id": str(org_id),
                    "finding_id": str(finding_id),
                    "linked_entity_type": linked_entity_type,
                    "linked_entity_id": str(linked_entity_id),
                    "notes": "Remediation M2 Step 3 backfill from journal_entry_ids",
                },
            )

    remaining = int(
        conn.execute(
            sa.text(
                """
                SELECT count(*)
                FROM audit_findings f
                LEFT JOIN evidence_links e ON e.finding_id = f.id
                WHERE e.id IS NULL
                """
            )
        ).scalar()
        or 0
    )
    if remaining > 0:
        raise RuntimeError(
            f"Evidence-link backfill incomplete: {remaining} finding(s) still unlinked."
        )


def downgrade() -> None:
    conn = op.get_bind()
    # Remove only backfill-created evidence (and cascading links)
    conn.execute(
        sa.text(
            """
            DELETE FROM evidence
            WHERE storage_key LIKE 'backfill://finding/%'
               OR (metadata->>'source') = 'remediation_m2_step3'
            """
        )
    )
