from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.audit import (
    EngagementTeamAssignmentHistory,
    EngagementTeamMember,
    OrganizationMember,
    User,
)
from app.services.engagement_team_constants import (
    ACTIVE_TEAM_STATUSES,
    ENGAGEMENT_ROLE_MIN_ORG_ROLE,
    ENGAGEMENT_SINGLE_SLOT_ROLES,
    ENGAGEMENT_TEAM_MANAGE_ORG_ROLES,
    ENGAGEMENT_TEAM_ROLES,
    ENGAGEMENT_TEAM_STATUSES,
    EXCLUDED_ORG_ROLES_FOR_TEAM,
    HISTORY_ACTIONS,
)
from app.services.project_access import get_owned_engagement
from app.services.tenant_context import TenantContext


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class TeamListResult:
    items: list[EngagementTeamMember]
    total: int


@dataclass(frozen=True)
class HistoryListResult:
    items: list[EngagementTeamAssignmentHistory]
    total: int


class EngagementTeamService:
    def list_team_members(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        role: str | None = None,
        status: str | None = "active",
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TeamListResult:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        query = (
            db.query(EngagementTeamMember)
            .options(
                joinedload(EngagementTeamMember.user),
                joinedload(EngagementTeamMember.assigner),
            )
            .filter(EngagementTeamMember.engagement_id == engagement.id)
        )

        if role:
            self._validate_team_role(role)
            query = query.filter(EngagementTeamMember.role == role.strip().lower())

        if status:
            self._validate_team_status(status)
            query = query.filter(EngagementTeamMember.status == status.strip().lower())

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.join(User, EngagementTeamMember.user_id == User.id).filter(
                or_(
                    func.lower(User.full_name).like(term),
                    func.lower(User.email).like(term),
                )
            )

        total = query.count()
        items = (
            query.order_by(EngagementTeamMember.role, EngagementTeamMember.assigned_at)
            .offset(offset)
            .limit(min(limit, 100))
            .all()
        )
        return TeamListResult(items=items, total=total)

    def assign_member(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        role: str,
        notes: str | None = None,
        change_reason: str | None = None,
    ) -> EngagementTeamMember:
        self._assert_can_manage_team(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        normalized_role = self._validate_team_role(role)

        org_member = self._resolve_org_member(db, engagement.organization_id, user_id)
        self._assert_assignee_eligible(org_member, normalized_role)

        existing = (
            db.query(EngagementTeamMember)
            .filter(
                EngagementTeamMember.engagement_id == engagement.id,
                EngagementTeamMember.user_id == user_id,
            )
            .first()
        )

        now = _now()
        if existing:
            if existing.status == "active" and existing.role == normalized_role:
                raise ValueError("This user is already assigned to this role on the engagement.")

            previous_role = existing.role if existing.status == "active" else None
            action = "reactivated" if existing.status == "removed" else "role_changed"

            if existing.status == "removed":
                existing.status = "active"
                existing.removed_at = None

            existing.role = normalized_role
            existing.notes = notes
            existing.assigned_by = tenant.user.id
            existing.assigned_at = now
            existing.organization_member_id = org_member.id
            existing.is_primary = normalized_role in ENGAGEMENT_SINGLE_SLOT_ROLES

            member = existing
            self._assert_single_slot_available(
                db, engagement.id, normalized_role, exclude_member_id=member.id
            )
            self._write_history(
                db,
                engagement_id=engagement.id,
                team_member_id=member.id,
                user_id=user_id,
                role=normalized_role,
                action=action,
                previous_role=previous_role,
                changed_by=tenant.user.id,
                change_reason=change_reason,
            )
        else:
            self._assert_single_slot_available(db, engagement.id, normalized_role)
            member = EngagementTeamMember(
                engagement_id=engagement.id,
                user_id=user_id,
                organization_member_id=org_member.id,
                role=normalized_role,
                status="active",
                is_primary=normalized_role in ENGAGEMENT_SINGLE_SLOT_ROLES,
                notes=notes,
                assigned_by=tenant.user.id,
                assigned_at=now,
            )
            db.add(member)
            db.flush()
            self._write_history(
                db,
                engagement_id=engagement.id,
                team_member_id=member.id,
                user_id=user_id,
                role=normalized_role,
                action="assigned",
                previous_role=None,
                changed_by=tenant.user.id,
                change_reason=change_reason,
            )

        db.commit()
        db.refresh(member)
        return self._load_member(db, member.id)

    def update_assignment(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        member_id: uuid.UUID,
        *,
        role: str | None = None,
        notes: str | None = None,
        change_reason: str | None = None,
    ) -> EngagementTeamMember:
        self._assert_can_manage_team(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        member = self._get_active_member(db, engagement.id, member_id)

        org_member = self._resolve_org_member(
            db, engagement.organization_id, member.user_id
        )

        previous_role = member.role
        if role is not None:
            normalized_role = self._validate_team_role(role)
            if normalized_role != member.role:
                self._assert_assignee_eligible(org_member, normalized_role)
                self._assert_single_slot_available(
                    db,
                    engagement.id,
                    normalized_role,
                    exclude_member_id=member.id,
                )
                member.role = normalized_role
                member.is_primary = normalized_role in ENGAGEMENT_SINGLE_SLOT_ROLES
                self._write_history(
                    db,
                    engagement_id=engagement.id,
                    team_member_id=member.id,
                    user_id=member.user_id,
                    role=normalized_role,
                    action="role_changed",
                    previous_role=previous_role,
                    changed_by=tenant.user.id,
                    change_reason=change_reason,
                )

        if notes is not None:
            member.notes = notes

        member.assigned_by = tenant.user.id
        db.commit()
        return self._load_member(db, member.id)

    def remove_member(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        member_id: uuid.UUID,
        *,
        change_reason: str | None = None,
    ) -> EngagementTeamMember:
        self._assert_can_manage_team(tenant)
        engagement = get_owned_engagement(db, engagement_id, tenant)
        member = self._get_active_member(db, engagement.id, member_id)

        member.status = "removed"
        member.removed_at = _now()
        member.is_primary = False

        self._write_history(
            db,
            engagement_id=engagement.id,
            team_member_id=member.id,
            user_id=member.user_id,
            role=member.role,
            action="removed",
            previous_role=member.role,
            changed_by=tenant.user.id,
            change_reason=change_reason,
        )

        db.commit()
        return self._load_member(db, member.id)

    def list_assignment_history(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
        *,
        user_id: uuid.UUID | None = None,
        role: str | None = None,
        action: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> HistoryListResult:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        query = (
            db.query(EngagementTeamAssignmentHistory)
            .options(
                joinedload(EngagementTeamAssignmentHistory.user),
                joinedload(EngagementTeamAssignmentHistory.changer),
            )
            .filter(EngagementTeamAssignmentHistory.engagement_id == engagement.id)
        )

        if user_id:
            query = query.filter(EngagementTeamAssignmentHistory.user_id == user_id)
        if role:
            self._validate_team_role(role)
            query = query.filter(
                EngagementTeamAssignmentHistory.role == role.strip().lower()
            )
        if action:
            normalized_action = action.strip().lower()
            if normalized_action not in HISTORY_ACTIONS:
                allowed = ", ".join(sorted(HISTORY_ACTIONS))
                raise ValueError(f"Invalid action. Allowed values: {allowed}.")
            query = query.filter(EngagementTeamAssignmentHistory.action == normalized_action)
        if date_from:
            query = query.filter(EngagementTeamAssignmentHistory.created_at >= date_from)
        if date_to:
            query = query.filter(EngagementTeamAssignmentHistory.created_at <= date_to)

        total = query.count()
        items = (
            query.order_by(EngagementTeamAssignmentHistory.created_at.desc())
            .offset(offset)
            .limit(min(limit, 100))
            .all()
        )
        return HistoryListResult(items=items, total=total)

    def get_team_summary(
        self,
        db: Session,
        tenant: TenantContext,
        engagement_id: uuid.UUID,
    ) -> dict:
        engagement = get_owned_engagement(db, engagement_id, tenant)
        rows = (
            db.query(EngagementTeamMember)
            .options(joinedload(EngagementTeamMember.user))
            .filter(
                EngagementTeamMember.engagement_id == engagement.id,
                EngagementTeamMember.status.in_(ACTIVE_TEAM_STATUSES),
            )
            .all()
        )

        by_role: dict[str, list[dict]] = {role: [] for role in sorted(ENGAGEMENT_TEAM_ROLES)}
        for row in rows:
            by_role[row.role].append(self._member_to_dict(row))

        partner = next((r for r in rows if r.role == "partner"), None)
        manager = next((r for r in rows if r.role == "audit_manager"), None)

        return {
            "engagement_id": engagement.id,
            "total_active": len(rows),
            "partner": self._member_to_dict(partner) if partner else None,
            "audit_manager": self._member_to_dict(manager) if manager else None,
            "by_role": by_role,
        }

    @staticmethod
    def _assert_can_manage_team(tenant: TenantContext) -> None:
        role = tenant.member_role or ""
        if role not in ENGAGEMENT_TEAM_MANAGE_ORG_ROLES:
            raise PermissionError(
                "You do not have permission to manage engagement team assignments."
            )

    @staticmethod
    def _validate_team_role(role: str) -> str:
        normalized = role.strip().lower()
        if normalized not in ENGAGEMENT_TEAM_ROLES:
            allowed = ", ".join(sorted(ENGAGEMENT_TEAM_ROLES))
            raise ValueError(f"Invalid engagement team role. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _validate_team_status(status: str) -> str:
        normalized = status.strip().lower()
        if normalized not in ENGAGEMENT_TEAM_STATUSES:
            allowed = ", ".join(sorted(ENGAGEMENT_TEAM_STATUSES))
            raise ValueError(f"Invalid status. Allowed values: {allowed}.")
        return normalized

    @staticmethod
    def _resolve_org_member(
        db: Session,
        organization_id: uuid.UUID | None,
        user_id: uuid.UUID,
    ) -> OrganizationMember:
        if not organization_id:
            raise ValueError(
                "This engagement is not linked to an organization. "
                "Team assignment requires an organization context."
            )

        member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
            .first()
        )
        if not member or member.status not in {"active", "invited"}:
            raise ValueError("User must be an active member of the engagement organization.")
        if member.role in EXCLUDED_ORG_ROLES_FOR_TEAM:
            raise ValueError(
                f"Users with organization role '{member.role}' cannot be assigned to an engagement team."
            )
        return member

    @staticmethod
    def _assert_assignee_eligible(org_member: OrganizationMember, engagement_role: str) -> None:
        allowed_org_roles = ENGAGEMENT_ROLE_MIN_ORG_ROLE.get(engagement_role, frozenset())
        if org_member.role not in allowed_org_roles:
            raise ValueError(
                f"Organization role '{org_member.role}' is not eligible for engagement role "
                f"'{engagement_role}'."
            )

    @staticmethod
    def _assert_single_slot_available(
        db: Session,
        engagement_id: uuid.UUID,
        role: str,
        *,
        exclude_member_id: uuid.UUID | None = None,
    ) -> None:
        if role not in ENGAGEMENT_SINGLE_SLOT_ROLES:
            return

        query = db.query(EngagementTeamMember).filter(
            EngagementTeamMember.engagement_id == engagement_id,
            EngagementTeamMember.role == role,
            EngagementTeamMember.status == "active",
        )
        if exclude_member_id:
            query = query.filter(EngagementTeamMember.id != exclude_member_id)

        if query.first():
            raise ValueError(
                f"An active {role.replace('_', ' ')} is already assigned to this engagement. "
                "Remove or reassign the existing member first."
            )

    @staticmethod
    def _get_active_member(
        db: Session, engagement_id: uuid.UUID, member_id: uuid.UUID
    ) -> EngagementTeamMember:
        member = (
            db.query(EngagementTeamMember)
            .filter(
                EngagementTeamMember.id == member_id,
                EngagementTeamMember.engagement_id == engagement_id,
            )
            .first()
        )
        if not member:
            raise ValueError("Team member not found.")
        if member.status not in ACTIVE_TEAM_STATUSES:
            raise ValueError("Team member is not active.")
        return member

    @staticmethod
    def _load_member(db: Session, member_id: uuid.UUID) -> EngagementTeamMember:
        member = (
            db.query(EngagementTeamMember)
            .options(
                joinedload(EngagementTeamMember.user),
                joinedload(EngagementTeamMember.assigner),
            )
            .filter(EngagementTeamMember.id == member_id)
            .first()
        )
        if not member:
            raise ValueError("Team member not found.")
        return member

    @staticmethod
    def _write_history(
        db: Session,
        *,
        engagement_id: uuid.UUID,
        team_member_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        action: str,
        previous_role: str | None,
        changed_by: uuid.UUID,
        change_reason: str | None,
    ) -> None:
        db.add(
            EngagementTeamAssignmentHistory(
                engagement_id=engagement_id,
                team_member_id=team_member_id,
                user_id=user_id,
                role=role,
                action=action,
                previous_role=previous_role,
                changed_by=changed_by,
                change_reason=change_reason,
            )
        )

    @staticmethod
    def member_to_out(member: EngagementTeamMember) -> dict:
        return EngagementTeamService._member_to_dict(member)

    @staticmethod
    def _member_to_dict(member: EngagementTeamMember | None) -> dict:
        if not member:
            return {}
        user = member.user
        assigner = member.assigner
        return {
            "id": member.id,
            "engagement_id": member.engagement_id,
            "user_id": member.user_id,
            "email": user.email if user else "",
            "full_name": user.full_name if user else "",
            "role": member.role,
            "status": member.status,
            "is_primary": member.is_primary,
            "notes": member.notes,
            "assigned_by": member.assigned_by,
            "assigned_by_name": assigner.full_name if assigner else None,
            "assigned_at": member.assigned_at,
            "removed_at": member.removed_at,
            "created_at": member.created_at,
            "updated_at": member.updated_at,
        }

    @staticmethod
    def history_to_out(entry: EngagementTeamAssignmentHistory) -> dict:
        user = entry.user
        changer = entry.changer
        return {
            "id": entry.id,
            "engagement_id": entry.engagement_id,
            "team_member_id": entry.team_member_id,
            "user_id": entry.user_id,
            "user_email": user.email if user else "",
            "user_full_name": user.full_name if user else "",
            "role": entry.role,
            "action": entry.action,
            "previous_role": entry.previous_role,
            "changed_by": entry.changed_by,
            "changed_by_name": changer.full_name if changer else None,
            "change_reason": entry.change_reason,
            "created_at": entry.created_at,
        }
