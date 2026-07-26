from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditFinding, AuditProject, Evidence, EvidenceLink
from app.services.evidence_constants import (
    EVIDENCE_CATEGORIES,
    EVIDENCE_MANAGE_ORG_ROLES,
    EVIDENCE_STATUSES,
    LINK_TYPES,
    LINKED_ENTITY_TYPES,
)
from app.services.file_storage_service import save_evidence_file
from app.services.storage import get_storage_backend
from app.services.project_access import get_owned_engagement, get_owned_project
from app.services.run_lock_guard import assert_project_allows_mutation, assert_run_allows_mutation
from app.services.tenant_context import TenantContext


@dataclass(frozen=True)
class EvidenceListResult:
    items: list[Evidence]
    total: int


class EvidenceService:
    def list_evidence(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        project_id: uuid.UUID | None = None,
        category: str | None = None,
        status: str | None = "active",
        search: str | None = None,
        current_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> EvidenceListResult:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        query = (
            db.query(Evidence)
            .options(joinedload(Evidence.uploader))
            .filter(Evidence.engagement_id == engagement.id)
        )

        if current_only:
            query = query.filter(Evidence.is_current.is_(True))
        if project_id:
            self._validate_project_on_engagement(db, engagement.id, project_id, tenant)
            query = query.filter(Evidence.project_id == project_id)
        if category:
            self._validate_category(category)
            query = query.filter(Evidence.category == category.strip().lower())
        if status:
            self._validate_status(status)
            query = query.filter(Evidence.status == status.strip().lower())
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Evidence.title).like(term),
                    func.lower(Evidence.file_name).like(term),
                    func.lower(Evidence.description).like(term),
                )
            )

        total = query.count()
        items = (
            query.order_by(Evidence.created_at.desc())
            .offset(offset)
            .limit(min(limit, 100))
            .all()
        )
        return EvidenceListResult(items=items, total=total)

    def upload_evidence(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        file_name: str,
        content: bytes,
        content_type: str | None,
        title: str,
        category: str = "other",
        description: str | None = None,
        project_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Evidence:
        self._assert_can_manage(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        if project_id:
            self._validate_project_on_engagement(db, engagement.id, project_id, tenant)
            assert_project_allows_mutation(db, project_id)

        normalized_category = self._validate_category(category)
        if not title.strip():
            raise ValueError("Title is required.")
        if not file_name.strip():
            raise ValueError("File name is required.")

        evidence = Evidence(
            engagement_id=engagement.id,
            project_id=project_id,
            organization_id=engagement.organization_id or tenant.organization_id,
            title=title.strip(),
            description=description,
            category=normalized_category,
            file_name=file_name.strip(),
            storage_key="pending",
            content_type=content_type,
            file_size_bytes=len(content),
            uploaded_by=tenant.user.id,
            metadata_=metadata or {},
        )
        db.add(evidence)
        db.flush()

        storage_key, file_hash = save_evidence_file(
            engagement.id, evidence.id, file_name, content
        )
        evidence.storage_key = storage_key
        evidence.file_hash = file_hash
        evidence.root_evidence_id = evidence.id

        db.commit()
        db.refresh(evidence)
        return self._load(db, evidence.id)

    def upload_new_version(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        evidence_id: uuid.UUID,
        *,
        file_name: str,
        content: bytes,
        content_type: str | None,
    ) -> Evidence:
        self._assert_can_manage(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        current = self._get_current_evidence(db, engagement.id, evidence_id)
        assert_run_allows_mutation(db, current.analysis_run_id)
        assert_project_allows_mutation(db, current.project_id)

        root_id = current.root_evidence_id or current.id
        max_version = (
            db.query(func.max(Evidence.version_number))
            .filter(Evidence.root_evidence_id == root_id)
            .scalar()
            or current.version_number
        )

        current.is_current = False

        new_version = Evidence(
            engagement_id=engagement.id,
            project_id=current.project_id,
            organization_id=current.organization_id,
            root_evidence_id=root_id,
            version_number=max_version + 1,
            is_current=True,
            title=current.title,
            description=current.description,
            category=current.category,
            file_name=file_name.strip(),
            storage_key="pending",
            content_type=content_type,
            file_size_bytes=len(content),
            file_hash=None,
            uploaded_by=tenant.user.id,
            metadata_=dict(current.metadata_ or {}),
        )
        db.add(new_version)
        db.flush()

        storage_key, file_hash = save_evidence_file(
            engagement.id, new_version.id, file_name, content
        )
        new_version.storage_key = storage_key
        new_version.file_hash = file_hash

        db.commit()
        return self._load(db, new_version.id)

    def list_versions(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        evidence_id: uuid.UUID,
    ) -> list[Evidence]:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        current = self._get_current_or_any(db, engagement.id, evidence_id)
        root_id = current.root_evidence_id or current.id
        return (
            db.query(Evidence)
            .options(joinedload(Evidence.uploader))
            .filter(Evidence.root_evidence_id == root_id)
            .order_by(Evidence.version_number.desc())
            .all()
        )

    def create_link(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        evidence_id: uuid.UUID,
        *,
        linked_entity_type: str,
        linked_entity_id: uuid.UUID,
        link_type: str = "reference",
        finding_id: uuid.UUID | None = None,
        workpaper_id: uuid.UUID | None = None,
        notes: str | None = None,
    ) -> EvidenceLink:
        self._assert_can_manage(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        evidence = self._get_current_or_any(db, engagement.id, evidence_id)
        assert_run_allows_mutation(db, evidence.analysis_run_id)
        assert_project_allows_mutation(db, evidence.project_id)

        entity_type = self._validate_entity_type(linked_entity_type)
        normalized_link = self._validate_link_type(link_type)

        if entity_type == "finding":
            self._validate_finding(db, engagement.id, linked_entity_id, tenant)
            finding_id = linked_entity_id
        elif entity_type == "workpaper":
            from app.models.audit import Workpaper

            wp = (
                db.query(Workpaper)
                .filter(
                    Workpaper.id == linked_entity_id,
                    Workpaper.engagement_id == engagement.id,
                )
                .first()
            )
            if not wp:
                raise ValueError("Workpaper not found on this engagement.")
            workpaper_id = linked_entity_id

        link = EvidenceLink(
            evidence_id=evidence.id,
            engagement_id=engagement.id,
            finding_id=finding_id,
            workpaper_id=workpaper_id,
            linked_entity_type=entity_type,
            linked_entity_id=linked_entity_id,
            link_type=normalized_link,
            notes=notes,
            created_by=tenant.user.id,
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    def list_links(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        evidence_id: uuid.UUID,
    ) -> list[EvidenceLink]:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        evidence = self._get_current_or_any(db, engagement.id, evidence_id)
        return (
            db.query(EvidenceLink)
            .filter(EvidenceLink.evidence_id == evidence.id)
            .order_by(EvidenceLink.created_at.desc())
            .all()
        )

    def get_download_path(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        evidence_id: uuid.UUID,
    ):
        engagement = get_owned_engagement(db, engagement_id, tenant)
        evidence = self._get_current_or_any(db, engagement.id, evidence_id)
        backend = get_storage_backend()
        if not evidence.storage_key or not backend.exists(evidence.storage_key):
            raise ValueError("Evidence file not found in storage.")
        path = backend.local_path(evidence.storage_key)
        if path is not None and path.is_file():
            return path, None, evidence
        return None, backend.read(evidence.storage_key), evidence

    @staticmethod
    def _assert_can_manage(tenant: TenantContext) -> None:
        role = tenant.member_role or ""
        if role not in EVIDENCE_MANAGE_ORG_ROLES:
            raise PermissionError("You do not have permission to manage evidence.")

    @staticmethod
    def _validate_category(category: str) -> str:
        normalized = category.strip().lower()
        if normalized not in EVIDENCE_CATEGORIES:
            allowed = ", ".join(sorted(EVIDENCE_CATEGORIES))
            raise ValueError(f"Invalid category. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _validate_status(status: str) -> str:
        normalized = status.strip().lower()
        if normalized not in EVIDENCE_STATUSES:
            allowed = ", ".join(sorted(EVIDENCE_STATUSES))
            raise ValueError(f"Invalid status. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _validate_entity_type(entity_type: str) -> str:
        normalized = entity_type.strip().lower()
        if normalized not in LINKED_ENTITY_TYPES:
            allowed = ", ".join(sorted(LINKED_ENTITY_TYPES))
            raise ValueError(f"Invalid entity type. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _validate_link_type(link_type: str) -> str:
        normalized = link_type.strip().lower()
        if normalized not in LINK_TYPES:
            allowed = ", ".join(sorted(LINK_TYPES))
            raise ValueError(f"Invalid link type. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _validate_project_on_engagement(
        db: Session,
        engagement_id: uuid.UUID,
        project_id: uuid.UUID,
        tenant: TenantContext,
    ) -> AuditProject:
        project = get_owned_project(db, project_id, tenant)
        if project.engagement_id != engagement_id:
            raise ValueError("Project does not belong to this engagement.")
        return project

    @staticmethod
    def _validate_finding(
        db: Session,
        engagement_id: uuid.UUID,
        finding_id: uuid.UUID,
        tenant: TenantContext,
    ) -> AuditFinding:
        finding = (
            db.query(AuditFinding)
            .join(AuditProject)
            .filter(
                AuditFinding.id == finding_id,
                AuditProject.engagement_id == engagement_id,
            )
            .first()
        )
        if not finding:
            raise ValueError("Finding not found on this engagement.")
        get_owned_project(db, finding.project_id, tenant)
        return finding

    @staticmethod
    def _get_current_evidence(
        db: Session, engagement_id: uuid.UUID, evidence_id: uuid.UUID
    ) -> Evidence:
        evidence = (
            db.query(Evidence)
            .filter(
                Evidence.id == evidence_id,
                Evidence.engagement_id == engagement_id,
                Evidence.is_current.is_(True),
            )
            .first()
        )
        if not evidence:
            raise ValueError("Evidence not found.")
        return evidence

    @staticmethod
    def _get_current_or_any(
        db: Session, engagement_id: uuid.UUID, evidence_id: uuid.UUID
    ) -> Evidence:
        evidence = (
            db.query(Evidence)
            .filter(
                Evidence.id == evidence_id,
                Evidence.engagement_id == engagement_id,
            )
            .first()
        )
        if not evidence:
            raise ValueError("Evidence not found.")
        return evidence

    @staticmethod
    def _load(db: Session, evidence_id: uuid.UUID) -> Evidence:
        evidence = (
            db.query(Evidence)
            .options(joinedload(Evidence.uploader))
            .filter(Evidence.id == evidence_id)
            .first()
        )
        if not evidence:
            raise ValueError("Evidence not found.")
        return evidence

    @staticmethod
    def to_out(evidence: Evidence) -> dict:
        uploader = evidence.uploader
        return {
            "id": evidence.id,
            "engagement_id": evidence.engagement_id,
            "project_id": evidence.project_id,
            "analysis_run_id": evidence.analysis_run_id,
            "root_evidence_id": evidence.root_evidence_id,
            "version_number": evidence.version_number,
            "is_current": evidence.is_current,
            "title": evidence.title,
            "description": evidence.description,
            "category": evidence.category,
            "file_name": evidence.file_name,
            "content_type": evidence.content_type,
            "file_size_bytes": evidence.file_size_bytes,
            "file_hash": evidence.file_hash,
            "status": evidence.status,
            "metadata": evidence.metadata_ or {},
            "uploaded_by": evidence.uploaded_by,
            "uploaded_by_name": uploader.full_name if uploader else None,
            "created_at": evidence.created_at,
            "updated_at": evidence.updated_at,
        }

    @staticmethod
    def link_to_out(link: EvidenceLink) -> dict:
        return {
            "id": link.id,
            "evidence_id": link.evidence_id,
            "engagement_id": link.engagement_id,
            "finding_id": link.finding_id,
            "workpaper_id": link.workpaper_id,
            "linked_entity_type": link.linked_entity_type,
            "linked_entity_id": link.linked_entity_id,
            "link_type": link.link_type,
            "notes": link.notes,
            "created_by": link.created_by,
            "created_at": link.created_at,
        }
