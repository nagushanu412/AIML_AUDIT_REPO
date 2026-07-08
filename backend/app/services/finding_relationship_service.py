from __future__ import annotations

import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditFinding, AuditProject, FindingRelationship
from app.services.finding_lifecycle_constants import FINDING_UPDATE_ROLES
from app.services.project_access import get_owned_engagement
from app.services.run_lock_guard import assert_project_allows_mutation
from app.services.tenant_context import TenantContext

RELATIONSHIP_TYPES = frozenset(
    {
        "related",
        "supports",
        "contradicts",
        "duplicate_of",
        "root_cause",
        "adjustment_impact",
    }
)


class FindingRelationshipService:
    def create_relationship(
        self,
        db: Session,
        tenant: TenantContext,
        finding_id: uuid.UUID,
        *,
        target_finding_id: uuid.UUID,
        relationship_type: str = "related",
        notes: str | None = None,
    ) -> FindingRelationship:
        self._assert_can_manage(tenant)
        source = self._get_owned_finding(db, tenant, finding_id)
        target = self._get_owned_finding(db, tenant, target_finding_id)

        if source.id == target.id:
            raise ValueError("A finding cannot be related to itself.")

        source_engagement = source.project.engagement_id
        target_engagement = target.project.engagement_id
        if source_engagement != target_engagement:
            raise ValueError("Findings must belong to the same engagement.")

        assert_project_allows_mutation(db, source.project_id)
        assert_project_allows_mutation(db, target.project_id)

        rel_type = self._validate_type(relationship_type)
        existing = (
            db.query(FindingRelationship)
            .filter(
                FindingRelationship.source_finding_id == source.id,
                FindingRelationship.target_finding_id == target.id,
                FindingRelationship.relationship_type == rel_type,
            )
            .first()
        )
        if existing:
            raise ValueError("This relationship already exists.")

        engagement = get_owned_engagement(db, source_engagement, tenant)
        row = FindingRelationship(
            engagement_id=engagement.id,
            organization_id=engagement.organization_id or tenant.organization_id,
            source_finding_id=source.id,
            target_finding_id=target.id,
            relationship_type=rel_type,
            notes=notes,
            created_by=tenant.user.id,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def list_relationships(
        self,
        db: Session,
        tenant: TenantContext,
        finding_id: uuid.UUID,
    ) -> list[FindingRelationship]:
        finding = self._get_owned_finding(db, tenant, finding_id)
        return (
            db.query(FindingRelationship)
            .filter(
                (FindingRelationship.source_finding_id == finding.id)
                | (FindingRelationship.target_finding_id == finding.id)
            )
            .order_by(FindingRelationship.created_at.desc())
            .all()
        )

    def delete_relationship(
        self,
        db: Session,
        tenant: TenantContext,
        finding_id: uuid.UUID,
        relationship_id: uuid.UUID,
    ) -> None:
        self._assert_can_manage(tenant)
        finding = self._get_owned_finding(db, tenant, finding_id)
        assert_project_allows_mutation(db, finding.project_id)

        row = (
            db.query(FindingRelationship)
            .filter(
                FindingRelationship.id == relationship_id,
                (
                    (FindingRelationship.source_finding_id == finding.id)
                    | (FindingRelationship.target_finding_id == finding.id)
                ),
            )
            .first()
        )
        if not row:
            raise ValueError("Relationship not found.")
        db.delete(row)
        db.commit()

    @staticmethod
    def _get_owned_finding(
        db: Session, tenant: TenantContext, finding_id: uuid.UUID
    ) -> AuditFinding:
        finding = (
            db.query(AuditFinding)
            .options(joinedload(AuditFinding.project))
            .join(AuditProject)
            .filter(AuditFinding.id == finding_id)
            .first()
        )
        if not finding:
            raise ValueError("Finding not found.")
        get_owned_engagement(db, finding.project.engagement_id, tenant)
        return finding

    @staticmethod
    def _assert_can_manage(tenant: TenantContext) -> None:
        if (tenant.member_role or "") not in FINDING_UPDATE_ROLES:
            raise PermissionError("You do not have permission to manage finding relationships.")

    @staticmethod
    def _validate_type(relationship_type: str) -> str:
        normalized = relationship_type.strip().lower()
        if normalized not in RELATIONSHIP_TYPES:
            allowed = ", ".join(sorted(RELATIONSHIP_TYPES))
            raise ValueError(f"Invalid relationship type. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def to_out(row: FindingRelationship) -> dict:
        return {
            "id": row.id,
            "engagement_id": row.engagement_id,
            "source_finding_id": row.source_finding_id,
            "target_finding_id": row.target_finding_id,
            "relationship_type": row.relationship_type,
            "notes": row.notes,
            "created_by": row.created_by,
            "created_at": row.created_at,
        }
