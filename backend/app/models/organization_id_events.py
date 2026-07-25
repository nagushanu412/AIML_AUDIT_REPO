"""SQLAlchemy before_insert listeners that denormalize organization_id.

Remediation M1 Step 2: no ORM insert path should leave organization_id unset
when a parent project/engagement (or member/user) can supply it.
"""
from __future__ import annotations

import uuid

from sqlalchemy import event, text
from sqlalchemy.engine import Connection

from app.models.audit import (
    Approval,
    AuditFinding,
    AuditLog,
    Client,
    EngagementEnabledModule,
    EngagementTeamMember,
    Evidence,
    EvidenceLink,
    FeatureFlag,
    FindingRelationship,
    JournalEntry,
    ModuleAnalysisRun,
    ProcurementInvoice,
    ProcurementRiskScore,
    ProcurementRuleResult,
    Report,
    RevenueInvoice,
    RevenueRiskScore,
    RevenueRuleResult,
    ReviewComment,
    RiskScore,
    RuleResult,
    Workpaper,
)


def _as_uuid(value: object | None) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _org_from_project(connection: Connection, project_id: object | None) -> uuid.UUID | None:
    pid = _as_uuid(project_id)
    if pid is None:
        return None
    return _as_uuid(
        connection.execute(
            text(
                """
                SELECT e.organization_id
                FROM audit_projects p
                JOIN audit_engagements e ON e.id = p.engagement_id
                WHERE p.id = :project_id
                """
            ),
            {"project_id": str(pid)},
        ).scalar()
    )


def _org_from_engagement(
    connection: Connection, engagement_id: object | None
) -> uuid.UUID | None:
    eid = _as_uuid(engagement_id)
    if eid is None:
        return None
    return _as_uuid(
        connection.execute(
            text(
                """
                SELECT organization_id
                FROM audit_engagements
                WHERE id = :engagement_id
                """
            ),
            {"engagement_id": str(eid)},
        ).scalar()
    )


def _org_from_organization_member(
    connection: Connection, organization_member_id: object | None
) -> uuid.UUID | None:
    mid = _as_uuid(organization_member_id)
    if mid is None:
        return None
    return _as_uuid(
        connection.execute(
            text(
                """
                SELECT organization_id
                FROM organization_members
                WHERE id = :member_id
                """
            ),
            {"member_id": str(mid)},
        ).scalar()
    )


def _org_from_user(connection: Connection, user_id: object | None) -> uuid.UUID | None:
    uid = _as_uuid(user_id)
    if uid is None:
        return None
    org_id = _as_uuid(
        connection.execute(
            text(
                """
                SELECT default_organization_id
                FROM users
                WHERE id = :user_id
                """
            ),
            {"user_id": str(uid)},
        ).scalar()
    )
    if org_id is not None:
        return org_id
    return _as_uuid(
        connection.execute(
            text(
                """
                SELECT organization_id
                FROM organization_members
                WHERE user_id = :user_id
                  AND status IN ('active', 'invited')
                ORDER BY created_at ASC
                LIMIT 1
                """
            ),
            {"user_id": str(uid)},
        ).scalar()
    )


def _require_org(target: object, org_id: uuid.UUID | None, source: str) -> None:
    if getattr(target, "organization_id", None):
        return
    if org_id is None:
        raise ValueError(
            f"{target.__class__.__name__}.organization_id could not be resolved "
            f"from {source}; set organization_id explicitly before insert."
        )
    target.organization_id = org_id


def _fill_from_project(mapper, connection: Connection, target) -> None:
    del mapper
    if target.organization_id:
        return
    _require_org(target, _org_from_project(connection, target.project_id), "project_id")


def _fill_from_engagement(mapper, connection: Connection, target) -> None:
    del mapper
    if target.organization_id:
        return
    _require_org(
        target,
        _org_from_engagement(connection, target.engagement_id),
        "engagement_id",
    )


def _fill_team_member(mapper, connection: Connection, target: EngagementTeamMember) -> None:
    del mapper
    if target.organization_id:
        return
    org_id = _org_from_organization_member(connection, target.organization_member_id)
    if org_id is None:
        org_id = _org_from_engagement(connection, target.engagement_id)
    _require_org(
        target,
        org_id,
        "organization_member_id/engagement_id",
    )


def _fill_audit_log(mapper, connection: Connection, target: AuditLog) -> None:
    del mapper
    if target.organization_id:
        return
    _require_org(target, _org_from_user(connection, target.user_id), "user_id")


def _fill_feature_flag(mapper, connection: Connection, target: FeatureFlag) -> None:
    del mapper, connection
    if target.organization_id:
        return
    raise ValueError(
        "FeatureFlag.organization_id is required at insert "
        "(global NULL scope is no longer allowed)."
    )


def _fill_client(mapper, connection: Connection, target: Client) -> None:
    del mapper
    if target.organization_id:
        return
    _require_org(target, _org_from_user(connection, target.user_id), "user_id")


_PROJECT_MODELS = (
    JournalEntry,
    RevenueInvoice,
    ProcurementInvoice,
    AuditFinding,
    RuleResult,
    RevenueRuleResult,
    ProcurementRuleResult,
    RiskScore,
    RevenueRiskScore,
    ProcurementRiskScore,
    Report,
)

_ENGAGEMENT_MODELS = (
    EvidenceLink,
    EngagementEnabledModule,
    ReviewComment,
    Approval,
    Evidence,
    Workpaper,
    FindingRelationship,
    ModuleAnalysisRun,
)


_LISTENERS_REGISTERED = False


def register_organization_id_listeners() -> None:
    """Idempotent registration of before_insert organization_id fillers."""
    global _LISTENERS_REGISTERED
    if _LISTENERS_REGISTERED:
        return
    for model in _PROJECT_MODELS:
        event.listen(model, "before_insert", _fill_from_project)
    for model in _ENGAGEMENT_MODELS:
        event.listen(model, "before_insert", _fill_from_engagement)
    event.listen(EngagementTeamMember, "before_insert", _fill_team_member)
    event.listen(AuditLog, "before_insert", _fill_audit_log)
    event.listen(FeatureFlag, "before_insert", _fill_feature_flag)
    event.listen(Client, "before_insert", _fill_client)
    _LISTENERS_REGISTERED = True


register_organization_id_listeners()
