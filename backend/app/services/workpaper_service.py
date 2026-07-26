from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.audit import Workpaper
from app.services.file_storage_service import save_workpaper_file
from app.services.storage import get_storage_backend
from app.services.project_access import get_owned_engagement, get_owned_project
from app.services.run_lock_guard import assert_project_allows_mutation, assert_run_allows_mutation
from app.services.tenant_context import TenantContext
from app.services.workpaper_constants import (
    WORKPAPER_CATEGORIES,
    WORKPAPER_MANAGE_ORG_ROLES,
    WORKPAPER_STATUSES,
)


@dataclass(frozen=True)
class WorkpaperListResult:
    items: list[Workpaper]
    total: int


class WorkpaperService:
    def list_workpapers(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        project_id: uuid.UUID | None = None,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
        current_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> WorkpaperListResult:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        query = (
            db.query(Workpaper)
            .options(joinedload(Workpaper.creator))
            .filter(Workpaper.engagement_id == engagement.id)
        )

        if current_only:
            query = query.filter(Workpaper.is_current.is_(True))
        if project_id:
            project = get_owned_project(db, project_id, tenant)
            if project.engagement_id != engagement.id:
                raise ValueError("Project does not belong to this engagement.")
            query = query.filter(Workpaper.project_id == project_id)
        if category:
            self._validate_category(category)
            query = query.filter(Workpaper.category == category.strip().lower())
        if status:
            self._validate_status(status)
            query = query.filter(Workpaper.status == status.strip().lower())
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Workpaper.title).like(term),
                    func.lower(Workpaper.reference_code).like(term),
                    func.lower(Workpaper.description).like(term),
                )
            )

        total = query.count()
        items = (
            query.order_by(Workpaper.reference_code, Workpaper.created_at.desc())
            .offset(offset)
            .limit(min(limit, 100))
            .all()
        )
        return WorkpaperListResult(items=items, total=total)

    def create_workpaper(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        reference_code: str,
        title: str,
        category: str = "testing",
        description: str | None = None,
        status: str = "draft",
        project_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Workpaper:
        self._assert_can_manage(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        if project_id:
            project = get_owned_project(db, project_id, tenant)
            if project.engagement_id != engagement.id:
                raise ValueError("Project does not belong to this engagement.")
            assert_project_allows_mutation(db, project_id)

        ref = reference_code.strip().upper()
        if not ref:
            raise ValueError("Reference code is required.")
        if not title.strip():
            raise ValueError("Title is required.")

        existing = (
            db.query(Workpaper)
            .filter(
                Workpaper.engagement_id == engagement.id,
                Workpaper.reference_code == ref,
                Workpaper.is_current.is_(True),
            )
            .first()
        )
        if existing:
            raise ValueError(f"Workpaper reference '{ref}' already exists on this engagement.")

        workpaper = Workpaper(
            engagement_id=engagement.id,
            project_id=project_id,
            organization_id=engagement.organization_id or tenant.organization_id,
            reference_code=ref,
            title=title.strip(),
            description=description,
            category=self._validate_category(category),
            status=self._validate_status(status),
            created_by=tenant.user.id,
            metadata_=metadata or {},
        )
        db.add(workpaper)
        db.flush()
        workpaper.root_workpaper_id = workpaper.id
        db.commit()
        return self._load(db, workpaper.id)

    def update_workpaper(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        workpaper_id: uuid.UUID,
        *,
        title: str | None = None,
        description: str | None = None,
        category: str | None = None,
        status: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Workpaper:
        self._assert_can_manage(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        workpaper = self._get_current(db, engagement.id, workpaper_id)
        assert_run_allows_mutation(db, workpaper.analysis_run_id)
        assert_project_allows_mutation(db, workpaper.project_id)

        if title is not None:
            if not title.strip():
                raise ValueError("Title cannot be empty.")
            workpaper.title = title.strip()
        if description is not None:
            workpaper.description = description
        if category is not None:
            workpaper.category = self._validate_category(category)
        if status is not None:
            workpaper.status = self._validate_status(status)
        if metadata is not None:
            workpaper.metadata_ = metadata

        db.commit()
        return self._load(db, workpaper.id)

    def upload_workpaper_file(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        workpaper_id: uuid.UUID,
        *,
        file_name: str,
        content: bytes,
        content_type: str | None,
        new_version: bool = False,
    ) -> Workpaper:
        self._assert_can_manage(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        current = self._get_current(db, engagement.id, workpaper_id)
        assert_run_allows_mutation(db, current.analysis_run_id)
        assert_project_allows_mutation(db, current.project_id)

        if new_version and current.storage_key:
            root_id = current.root_workpaper_id or current.id
            max_version = (
                db.query(func.max(Workpaper.version_number))
                .filter(Workpaper.root_workpaper_id == root_id)
                .scalar()
                or current.version_number
            )
            current.is_current = False
            workpaper = Workpaper(
                engagement_id=engagement.id,
                project_id=current.project_id,
                organization_id=current.organization_id,
                root_workpaper_id=root_id,
                version_number=max_version + 1,
                is_current=True,
                reference_code=current.reference_code,
                title=current.title,
                description=current.description,
                category=current.category,
                status=current.status,
                created_by=tenant.user.id,
                metadata_=dict(current.metadata_ or {}),
            )
            db.add(workpaper)
            db.flush()
        else:
            workpaper = current

        storage_key, file_hash = save_workpaper_file(
            engagement.id, workpaper.id, file_name, content
        )
        workpaper.file_name = file_name.strip()
        workpaper.storage_key = storage_key
        workpaper.file_hash = file_hash
        workpaper.content_type = content_type
        workpaper.file_size_bytes = len(content)
        if not workpaper.root_workpaper_id:
            workpaper.root_workpaper_id = workpaper.id

        db.commit()
        return self._load(db, workpaper.id)

    def list_versions(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        workpaper_id: uuid.UUID,
    ) -> list[Workpaper]:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        current = self._get_any(db, engagement.id, workpaper_id)
        root_id = current.root_workpaper_id or current.id
        return (
            db.query(Workpaper)
            .options(joinedload(Workpaper.creator))
            .filter(Workpaper.root_workpaper_id == root_id)
            .order_by(Workpaper.version_number.desc())
            .all()
        )

    def get_download_path(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        workpaper_id: uuid.UUID,
    ):
        engagement = get_owned_engagement(db, engagement_id, tenant)
        workpaper = self._get_any(db, engagement.id, workpaper_id)
        backend = get_storage_backend()
        if not workpaper.storage_key or not backend.exists(workpaper.storage_key):
            raise ValueError("Workpaper file not found in storage.")
        path = backend.local_path(workpaper.storage_key)
        if path is not None and path.is_file():
            return path, None, workpaper
        return None, backend.read(workpaper.storage_key), workpaper

    @staticmethod
    def _assert_can_manage(tenant: TenantContext) -> None:
        role = tenant.member_role or ""
        if role not in WORKPAPER_MANAGE_ORG_ROLES:
            raise PermissionError("You do not have permission to manage workpapers.")

    @staticmethod
    def _validate_category(category: str) -> str:
        normalized = category.strip().lower()
        if normalized not in WORKPAPER_CATEGORIES:
            allowed = ", ".join(sorted(WORKPAPER_CATEGORIES))
            raise ValueError(f"Invalid category. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _validate_status(status: str) -> str:
        normalized = status.strip().lower()
        if normalized not in WORKPAPER_STATUSES:
            allowed = ", ".join(sorted(WORKPAPER_STATUSES))
            raise ValueError(f"Invalid status. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _get_current(
        db: Session, engagement_id: uuid.UUID, workpaper_id: uuid.UUID
    ) -> Workpaper:
        workpaper = (
            db.query(Workpaper)
            .filter(
                Workpaper.id == workpaper_id,
                Workpaper.engagement_id == engagement_id,
                Workpaper.is_current.is_(True),
            )
            .first()
        )
        if not workpaper:
            raise ValueError("Workpaper not found.")
        return workpaper

    @staticmethod
    def _get_any(
        db: Session, engagement_id: uuid.UUID, workpaper_id: uuid.UUID
    ) -> Workpaper:
        workpaper = (
            db.query(Workpaper)
            .filter(
                Workpaper.id == workpaper_id,
                Workpaper.engagement_id == engagement_id,
            )
            .first()
        )
        if not workpaper:
            raise ValueError("Workpaper not found.")
        return workpaper

    @staticmethod
    def _load(db: Session, workpaper_id: uuid.UUID) -> Workpaper:
        workpaper = (
            db.query(Workpaper)
            .options(joinedload(Workpaper.creator))
            .filter(Workpaper.id == workpaper_id)
            .first()
        )
        if not workpaper:
            raise ValueError("Workpaper not found.")
        return workpaper

    @staticmethod
    def to_out(workpaper: Workpaper) -> dict:
        creator = workpaper.creator
        return {
            "id": workpaper.id,
            "engagement_id": workpaper.engagement_id,
            "project_id": workpaper.project_id,
            "analysis_run_id": workpaper.analysis_run_id,
            "root_workpaper_id": workpaper.root_workpaper_id,
            "version_number": workpaper.version_number,
            "is_current": workpaper.is_current,
            "reference_code": workpaper.reference_code,
            "title": workpaper.title,
            "description": workpaper.description,
            "category": workpaper.category,
            "file_name": workpaper.file_name,
            "content_type": workpaper.content_type,
            "file_size_bytes": workpaper.file_size_bytes,
            "file_hash": workpaper.file_hash,
            "has_file": bool(workpaper.storage_key),
            "status": workpaper.status,
            "metadata": workpaper.metadata_ or {},
            "created_by": workpaper.created_by,
            "created_by_name": creator.full_name if creator else None,
            "created_at": workpaper.created_at,
            "updated_at": workpaper.updated_at,
        }
