"""Remediation Milestone 1 Step 3 — multi-tenant HTTP isolation matrix.

Firm A creates tenant-scoped records; Firm B's token must never receive 200
(or a list leak) when targeting those records via the real API.
"""

from __future__ import annotations

import io
import uuid
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import SessionLocal, validate_database_connection
from app.main import app
from app.models.audit import (
    Approval,
    AuditFinding,
    AuditLog,
    EngagementEnabledModule,
    EngagementTeamMember,
    EvidenceLink,
    FindingRelationship,
    JournalEntry,
    ModuleAnalysisRun,
    OrganizationMember,
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
)
from app.models.organization_id_events import register_organization_id_listeners

register_organization_id_listeners()

client = TestClient(app)

MODULE_CODES = (
    "JOURNAL_ENTRY_TESTING",
    "REVENUE_TESTING",
    "PROCUREMENT_TESTING",
)


def _db_available() -> bool:
    try:
        validate_database_connection()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not available")


def _assert_denied(response) -> None:
    assert response.status_code in (403, 404), (
        f"expected 403/404, got {response.status_code}: {response.text[:300]}"
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _xlsx_from_rows(rows: list[dict]) -> bytes:
    buf = io.BytesIO()
    pd.DataFrame(rows).to_excel(buf, index=False)
    return buf.getvalue()


def _journal_xlsx() -> bytes:
    return _xlsx_from_rows(
        [
            {
                "Journal_ID": "ISO-J1",
                "Posting_Date": "2026-04-01",
                "Account_Code": "1000",
                "Account_Name": "Cash",
                "Amount": 150000,
                "Debit_Credit": "Debit",
                "User_ID": "auditor1",
                "Description": "isolation seed",
            }
        ]
    )


def _revenue_xlsx() -> bytes:
    return _xlsx_from_rows(
        [
            {
                "Invoice_No": "INV-ISO-1",
                "Invoice_Date": "2026-04-01",
                "Customer_Name": "Acme",
                "Taxable_Amount": 1000,
                "GST_Amount": 180,
                "Total_Amount": 1180,
            }
        ]
    )


def _procurement_xlsx() -> bytes:
    return _xlsx_from_rows(
        [
            {
                "Invoice_No": "PINV-ISO-1",
                "Invoice_Date": "2026-04-01",
                "Vendor_Name": "VendorCo",
                "Taxable_Amount": 2000,
                "GST_Amount": 360,
                "Total_Amount": 2360,
            }
        ]
    )


@pytest.fixture(scope="module")
def isolation_world():
    """Two firms + Firm A hierarchy and seeded tenant records."""
    suffix = uuid.uuid4().hex[:10]
    reg_a = client.post(
        "/auth/register",
        json={
            "email": f"firm-a-{suffix}@example.com",
            "password": "IsolationA2026!",
            "full_name": "Firm A Owner",
            "company_name": f"Firm A Isolation {suffix}",
        },
    )
    assert reg_a.status_code == 201, reg_a.text
    body_a = reg_a.json()
    token_a = body_a["access_token"]
    org_a = uuid.UUID(str(body_a["organization_id"]))
    user_a = uuid.UUID(str(body_a["user_id"]))
    headers_a = _auth(token_a)

    reg_b = client.post(
        "/auth/register",
        json={
            "email": f"firm-b-{suffix}@example.com",
            "password": "IsolationB2026!",
            "full_name": "Firm B Owner",
            "company_name": f"Firm B Isolation {suffix}",
        },
    )
    assert reg_b.status_code == 201, reg_b.text
    body_b = reg_b.json()
    token_b = body_b["access_token"]
    org_b = uuid.UUID(str(body_b["organization_id"]))
    headers_b = _auth(token_b)

    c_resp = client.post(
        "/clients",
        headers=headers_a,
        json={"name": f"Client A {suffix}", "industry": "Manufacturing"},
    )
    assert c_resp.status_code == 201, c_resp.text
    client_id = c_resp.json()["id"]

    e_resp = client.post(
        "/engagements",
        headers=headers_a,
        json={
            "client_id": client_id,
            "financial_year": "FY 2026-27",
            "financial_year_end": "2027-03-31",
            "audit_type": "Statutory",
            "status": "planned",
            "large_value_threshold": "100000.00",
        },
    )
    assert e_resp.status_code == 201, e_resp.text
    engagement_id = e_resp.json()["id"]

    projects: dict[str, str] = {}
    for ptype, name in (
        ("journal_testing", "Journal Isolation"),
        ("revenue_testing", "Revenue Isolation"),
        ("procurement_testing", "Procurement Isolation"),
    ):
        p_resp = client.post(
            "/projects",
            headers=headers_a,
            json={
                "engagement_id": engagement_id,
                "name": name,
                "project_type": ptype,
                "status": "active",
            },
        )
        assert p_resp.status_code == 201, p_resp.text
        projects[ptype] = p_resp.json()["id"]

    # Module uploads (Firm A creates invoice/entry rows via real API)
    up_j = client.post(
        "/upload",
        headers=headers_a,
        params={"project_id": projects["journal_testing"]},
        files={
            "file": (
                "journal.xlsx",
                _journal_xlsx(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert up_j.status_code == 200, up_j.text

    up_r = client.post(
        "/revenue/upload",
        headers=headers_a,
        params={"project_id": projects["revenue_testing"]},
        files={
            "file": (
                "revenue.xlsx",
                _revenue_xlsx(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert up_r.status_code == 200, up_r.text

    up_p = client.post(
        "/procurement/upload",
        headers=headers_a,
        params={"project_id": projects["procurement_testing"]},
        files={
            "file": (
                "procurement.xlsx",
                _procurement_xlsx(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert up_p.status_code == 200, up_p.text

    # Enable a module + create evidence/workpaper/run via API
    mod = client.post(
        f"/engagements/{engagement_id}/modules/JOURNAL_ENTRY_TESTING/enable",
        headers=headers_a,
    )
    assert mod.status_code in (200, 201), mod.text

    ev = client.post(
        f"/engagements/{engagement_id}/evidence",
        headers=headers_a,
        data={"title": "Isolation Evidence", "category": "other"},
        files={"file": ("note.txt", b"isolation evidence", "text/plain")},
    )
    assert ev.status_code == 201, ev.text
    evidence_id = ev.json()["id"]

    wp = client.post(
        f"/engagements/{engagement_id}/workpapers",
        headers=headers_a,
        json={
            "reference_code": f"WP-{suffix[:6]}",
            "title": "Isolation Workpaper",
            "category": "testing",
            "project_id": projects["journal_testing"],
        },
    )
    assert wp.status_code == 201, wp.text
    workpaper_id = wp.json()["id"]

    run = client.post(
        f"/engagements/{engagement_id}/runs",
        headers=headers_a,
        json={
            "module_code": "JOURNAL_ENTRY_TESTING",
            "run_name": f"Isolation Run {suffix}",
            "project_id": projects["journal_testing"],
        },
    )
    assert run.status_code == 201, run.text
    run_id = run.json()["id"]

    # Seed remaining tenant rows (rules/risk/findings/reports/links/etc.)
    db: Session = SessionLocal()
    try:
        journal_project = uuid.UUID(projects["journal_testing"])
        revenue_project = uuid.UUID(projects["revenue_testing"])
        procurement_project = uuid.UUID(projects["procurement_testing"])
        eng_uuid = uuid.UUID(engagement_id)
        evid_uuid = uuid.UUID(evidence_id)

        je = (
            db.query(JournalEntry)
            .filter(JournalEntry.project_id == journal_project)
            .first()
        )
        assert je is not None
        rev = (
            db.query(RevenueInvoice)
            .filter(RevenueInvoice.project_id == revenue_project)
            .first()
        )
        assert rev is not None
        proc = (
            db.query(ProcurementInvoice)
            .filter(ProcurementInvoice.project_id == procurement_project)
            .first()
        )
        assert proc is not None

        rr = RuleResult(
            project_id=journal_project,
            organization_id=org_a,
            journal_entry_id=je.id,
            rule_code="LARGE_VALUE",
            rule_name="Large Value",
            triggered=True,
            details="seed",
        )
        db.add(rr)
        rs = RiskScore(
            project_id=journal_project,
            organization_id=org_a,
            journal_entry_id=je.id,
            total_score=40,
            risk_category="high",
            rule_breakdown={"LARGE_VALUE": 40},
        )
        db.add(rs)

        rrr = RevenueRuleResult(
            project_id=revenue_project,
            organization_id=org_a,
            revenue_invoice_id=rev.id,
            rule_code="REV_DUPLICATE_INVOICE",
            rule_name="Duplicate Invoice",
            triggered=True,
        )
        db.add(rrr)
        rrs = RevenueRiskScore(
            project_id=revenue_project,
            organization_id=org_a,
            revenue_invoice_id=rev.id,
            total_score=25,
            risk_category="medium",
            rule_breakdown={},
        )
        db.add(rrs)

        prr = ProcurementRuleResult(
            project_id=procurement_project,
            organization_id=org_a,
            procurement_invoice_id=proc.id,
            rule_code="PROC_DUPLICATE_PAYMENT",
            rule_name="Duplicate Vendor Payment",
            triggered=True,
        )
        db.add(prr)
        prs = ProcurementRiskScore(
            project_id=procurement_project,
            organization_id=org_a,
            procurement_invoice_id=proc.id,
            total_score=30,
            risk_category="medium",
            rule_breakdown={},
        )
        db.add(prs)

        finding = AuditFinding(
            project_id=journal_project,
            organization_id=org_a,
            rule_code="LARGE_VALUE",
            finding_title="Isolation Finding A",
            observation="Seed finding for isolation matrix",
            risk_level="high",
            impact="Material",
            recommendation="Investigate",
            affected_count=1,
            source_record_ids=[str(je.id)],
            status="open",
        )
        finding2 = AuditFinding(
            project_id=journal_project,
            organization_id=org_a,
            rule_code="WEEKEND",
            finding_title="Isolation Finding A2",
            observation="Second finding for relationships",
            risk_level="medium",
            impact="Moderate",
            recommendation="Review",
            affected_count=1,
            source_record_ids=[str(je.id)],
            status="open",
        )
        db.add(finding)
        db.add(finding2)
        db.flush()

        report = Report(
            project_id=journal_project,
            organization_id=org_a,
            report_type="findings",
            file_name="isolation-report.xlsx",
            status="ready",
            metadata_={},
        )
        db.add(report)

        link = EvidenceLink(
            evidence_id=evid_uuid,
            engagement_id=eng_uuid,
            organization_id=org_a,
            finding_id=finding.id,
            linked_entity_type="finding",
            linked_entity_id=finding.id,
            link_type="supports",
            created_by=user_a,
        )
        db.add(link)

        rel = FindingRelationship(
            engagement_id=eng_uuid,
            organization_id=org_a,
            source_finding_id=finding.id,
            target_finding_id=finding2.id,
            relationship_type="related",
            created_by=user_a,
        )
        db.add(rel)

        comment = ReviewComment(
            engagement_id=eng_uuid,
            organization_id=org_a,
            finding_id=finding.id,
            project_id=journal_project,
            comment_type="review",
            body="Isolation review comment",
            status="open",
            created_by=user_a,
        )
        db.add(comment)

        approval = Approval(
            engagement_id=eng_uuid,
            organization_id=org_a,
            finding_id=finding.id,
            project_id=journal_project,
            approval_type="finding",
            status="pending",
            comments="Isolation approval",
            created_by=user_a,
        )
        db.add(approval)

        org_member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == org_a,
                OrganizationMember.user_id == user_a,
            )
            .first()
        )
        assert org_member is not None
        team = EngagementTeamMember(
            engagement_id=eng_uuid,
            organization_id=org_a,
            user_id=user_a,
            organization_member_id=org_member.id,
            role="partner",
            status="active",
            is_primary=True,
            assigned_by=user_a,
        )
        db.add(team)

        enabled = (
            db.query(EngagementEnabledModule)
            .filter(EngagementEnabledModule.engagement_id == eng_uuid)
            .first()
        )
        assert enabled is not None

        analysis_run = (
            db.query(ModuleAnalysisRun)
            .filter(ModuleAnalysisRun.id == uuid.UUID(run_id))
            .first()
        )
        assert analysis_run is not None

        audit_log = AuditLog(
            organization_id=org_a,
            user_id=user_a,
            action="isolation.seed",
            entity_type="audit_finding",
            entity_id=finding.id,
            details={"marker": f"firm-a-{suffix}"},
        )
        db.add(audit_log)
        db.commit()

        ids = SimpleNamespace(
            org_a=org_a,
            org_b=org_b,
            user_a=user_a,
            token_a=token_a,
            token_b=token_b,
            headers_a=headers_a,
            headers_b=headers_b,
            client_id=client_id,
            engagement_id=engagement_id,
            projects=projects,
            journal_entry_id=str(je.id),
            revenue_invoice_id=str(rev.id),
            procurement_invoice_id=str(proc.id),
            rule_result_id=str(rr.id),
            risk_score_id=str(rs.id),
            revenue_rule_result_id=str(rrr.id),
            revenue_risk_score_id=str(rrs.id),
            procurement_rule_result_id=str(prr.id),
            procurement_risk_score_id=str(prs.id),
            finding_id=str(finding.id),
            finding2_id=str(finding2.id),
            report_id=str(report.id),
            evidence_id=evidence_id,
            evidence_link_id=str(link.id),
            workpaper_id=workpaper_id,
            relationship_id=str(rel.id),
            comment_id=str(comment.id),
            approval_id=str(approval.id),
            team_member_id=str(team.id),
            enabled_module_id=str(enabled.id),
            run_id=run_id,
            audit_log_entity_id=str(finding.id),
            marker=f"firm-a-{suffix}",
        )
    finally:
        db.close()

    return ids


# ---------------------------------------------------------------------------
# feature_flags — no HTTP surface
# ---------------------------------------------------------------------------


@requires_db
def test_feature_flags_have_no_http_api_surface():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    assert not any("feature_flag" in p for p in paths)


# ---------------------------------------------------------------------------
# Cross-tenant denial matrix (tables with HTTP surfaces)
# ---------------------------------------------------------------------------


@requires_db
@pytest.mark.parametrize(
    "case_id,method,path_template,kwargs_builder",
    [
        (
            "clients_get",
            "GET",
            "/clients/{client_id}",
            lambda w: {"client_id": w.client_id},
        ),
        (
            "clients_patch",
            "PATCH",
            "/clients/{client_id}",
            lambda w: {"client_id": w.client_id, "json": {"name": "Hijack"}},
        ),
        (
            "clients_delete",
            "DELETE",
            "/clients/{client_id}",
            lambda w: {"client_id": w.client_id},
        ),
        (
            "engagements_get",
            "GET",
            "/engagements/{engagement_id}",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "engagements_patch",
            "PATCH",
            "/engagements/{engagement_id}",
            lambda w: {
                "engagement_id": w.engagement_id,
                "json": {"status": "in_progress"},
            },
        ),
        (
            "engagements_delete",
            "DELETE",
            "/engagements/{engagement_id}",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "projects_get",
            "GET",
            "/projects/{project_id}",
            lambda w: {"project_id": w.projects["journal_testing"]},
        ),
        (
            "projects_patch",
            "PATCH",
            "/projects/{project_id}",
            lambda w: {
                "project_id": w.projects["journal_testing"],
                "json": {"name": "Hijacked"},
            },
        ),
        (
            "projects_delete",
            "DELETE",
            "/projects/{project_id}",
            lambda w: {"project_id": w.projects["journal_testing"]},
        ),
        (
            "journal_upload",
            "POST",
            "/upload",
            lambda w: {
                "params": {"project_id": w.projects["journal_testing"]},
                "files": {
                    "file": (
                        "j.xlsx",
                        _journal_xlsx(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            },
        ),
        (
            "rule_results_list",
            "GET",
            "/rule-results",
            lambda w: {"params": {"project_id": w.projects["journal_testing"]}},
        ),
        (
            "run_rules",
            "POST",
            "/run-rules",
            lambda w: {"params": {"project_id": w.projects["journal_testing"]}},
        ),
        (
            "risk_scores_list",
            "GET",
            "/risk-scores",
            lambda w: {"params": {"project_id": w.projects["journal_testing"]}},
        ),
        (
            "run_risk",
            "POST",
            "/run-risk",
            lambda w: {"params": {"project_id": w.projects["journal_testing"]}},
        ),
        (
            "findings_list_journal",
            "GET",
            "/findings",
            lambda w: {"params": {"project_id": w.projects["journal_testing"]}},
        ),
        (
            "generate_findings_journal",
            "POST",
            "/generate-findings",
            lambda w: {"params": {"project_id": w.projects["journal_testing"]}},
        ),
        (
            "reports_list",
            "GET",
            "/reports",
            lambda w: {"params": {"project_id": w.projects["journal_testing"]}},
        ),
        (
            "reports_generate",
            "POST",
            "/reports/generate",
            lambda w: {
                "params": {
                    "project_id": w.projects["journal_testing"],
                    "report_type": "findings",
                }
            },
        ),
        (
            "reports_download",
            "GET",
            "/reports/{report_id}/download",
            lambda w: {"report_id": w.report_id},
        ),
        (
            "revenue_upload",
            "POST",
            "/revenue/upload",
            lambda w: {
                "params": {"project_id": w.projects["revenue_testing"]},
                "files": {
                    "file": (
                        "r.xlsx",
                        _revenue_xlsx(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            },
        ),
        (
            "revenue_run_rules",
            "POST",
            "/revenue/run-rules",
            lambda w: {"params": {"project_id": w.projects["revenue_testing"]}},
        ),
        (
            "revenue_run_risk",
            "POST",
            "/revenue/run-risk",
            lambda w: {"params": {"project_id": w.projects["revenue_testing"]}},
        ),
        (
            "revenue_risk_scores",
            "GET",
            "/revenue/risk-scores",
            lambda w: {"params": {"project_id": w.projects["revenue_testing"]}},
        ),
        (
            "revenue_findings",
            "GET",
            "/revenue/findings",
            lambda w: {"params": {"project_id": w.projects["revenue_testing"]}},
        ),
        (
            "revenue_generate_findings",
            "POST",
            "/revenue/generate-findings",
            lambda w: {"params": {"project_id": w.projects["revenue_testing"]}},
        ),
        (
            "procurement_upload",
            "POST",
            "/procurement/upload",
            lambda w: {
                "params": {"project_id": w.projects["procurement_testing"]},
                "files": {
                    "file": (
                        "p.xlsx",
                        _procurement_xlsx(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            },
        ),
        (
            "procurement_run_rules",
            "POST",
            "/procurement/run-rules",
            lambda w: {"params": {"project_id": w.projects["procurement_testing"]}},
        ),
        (
            "procurement_run_risk",
            "POST",
            "/procurement/run-risk",
            lambda w: {"params": {"project_id": w.projects["procurement_testing"]}},
        ),
        (
            "procurement_risk_scores",
            "GET",
            "/procurement/risk-scores",
            lambda w: {"params": {"project_id": w.projects["procurement_testing"]}},
        ),
        (
            "procurement_findings",
            "GET",
            "/procurement/findings",
            lambda w: {"params": {"project_id": w.projects["procurement_testing"]}},
        ),
        (
            "procurement_generate_findings",
            "POST",
            "/procurement/generate-findings",
            lambda w: {"params": {"project_id": w.projects["procurement_testing"]}},
        ),
        (
            "finding_get",
            "GET",
            "/findings/{finding_id}",
            lambda w: {"finding_id": w.finding_id},
        ),
        (
            "finding_status",
            "PATCH",
            "/findings/{finding_id}/status",
            lambda w: {
                "finding_id": w.finding_id,
                "json": {"status": "under_review", "change_reason": "x"},
            },
        ),
        (
            "finding_history",
            "GET",
            "/findings/{finding_id}/history",
            lambda w: {"finding_id": w.finding_id},
        ),
        (
            "engagement_findings_list",
            "GET",
            "/engagements/{engagement_id}/findings",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "relationships_list",
            "GET",
            "/findings/{finding_id}/relationships",
            lambda w: {"finding_id": w.finding_id},
        ),
        (
            "relationships_create",
            "POST",
            "/findings/{finding_id}/relationships",
            lambda w: {
                "finding_id": w.finding_id,
                "json": {
                    "target_finding_id": w.finding2_id,
                    "relationship_type": "related",
                },
            },
        ),
        (
            "relationships_delete",
            "DELETE",
            "/findings/{finding_id}/relationships/{relationship_id}",
            lambda w: {
                "finding_id": w.finding_id,
                "relationship_id": w.relationship_id,
            },
        ),
        (
            "comments_list",
            "GET",
            "/findings/{finding_id}/comments",
            lambda w: {"finding_id": w.finding_id},
        ),
        (
            "comments_create",
            "POST",
            "/findings/{finding_id}/comments",
            lambda w: {
                "finding_id": w.finding_id,
                "json": {"body": "cross-tenant comment", "comment_type": "review"},
            },
        ),
        (
            "approvals_list",
            "GET",
            "/findings/{finding_id}/approvals",
            lambda w: {"finding_id": w.finding_id},
        ),
        (
            "approvals_create",
            "POST",
            "/findings/{finding_id}/approve",
            lambda w: {"finding_id": w.finding_id, "json": {"comments": "no"}},
        ),
        (
            "approvals_decide",
            "PATCH",
            "/approvals/{approval_id}",
            lambda w: {
                "approval_id": w.approval_id,
                "json": {"status": "approved", "comments": "no"},
            },
        ),
        (
            "evidence_list",
            "GET",
            "/engagements/{engagement_id}/evidence",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "evidence_download",
            "GET",
            "/engagements/{engagement_id}/evidence/{evidence_id}/download",
            lambda w: {
                "engagement_id": w.engagement_id,
                "evidence_id": w.evidence_id,
            },
        ),
        (
            "evidence_links_list",
            "GET",
            "/engagements/{engagement_id}/evidence/{evidence_id}/links",
            lambda w: {
                "engagement_id": w.engagement_id,
                "evidence_id": w.evidence_id,
            },
        ),
        (
            "evidence_links_create",
            "POST",
            "/engagements/{engagement_id}/evidence/{evidence_id}/links",
            lambda w: {
                "engagement_id": w.engagement_id,
                "evidence_id": w.evidence_id,
                "json": {
                    "linked_entity_type": "finding",
                    "linked_entity_id": w.finding_id,
                    "link_type": "supports",
                    "finding_id": w.finding_id,
                },
            },
        ),
        (
            "workpapers_list",
            "GET",
            "/engagements/{engagement_id}/workpapers",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "workpapers_patch",
            "PATCH",
            "/engagements/{engagement_id}/workpapers/{workpaper_id}",
            lambda w: {
                "engagement_id": w.engagement_id,
                "workpaper_id": w.workpaper_id,
                "json": {"title": "Hijacked WP"},
            },
        ),
        (
            "workpapers_download",
            "GET",
            "/engagements/{engagement_id}/workpapers/{workpaper_id}/download",
            lambda w: {
                "engagement_id": w.engagement_id,
                "workpaper_id": w.workpaper_id,
            },
        ),
        (
            "modules_list",
            "GET",
            "/engagements/{engagement_id}/modules",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "modules_disable",
            "POST",
            "/engagements/{engagement_id}/modules/JOURNAL_ENTRY_TESTING/disable",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "team_list",
            "GET",
            "/engagements/{engagement_id}/team",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "team_summary",
            "GET",
            "/engagements/{engagement_id}/team/summary",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "team_patch",
            "PATCH",
            "/engagements/{engagement_id}/team/{member_id}",
            lambda w: {
                "engagement_id": w.engagement_id,
                "member_id": w.team_member_id,
                "json": {"role": "auditor"},
            },
        ),
        (
            "team_delete",
            "DELETE",
            "/engagements/{engagement_id}/team/{member_id}",
            lambda w: {
                "engagement_id": w.engagement_id,
                "member_id": w.team_member_id,
            },
        ),
        (
            "runs_list",
            "GET",
            "/engagements/{engagement_id}/runs",
            lambda w: {"engagement_id": w.engagement_id},
        ),
        (
            "runs_get",
            "GET",
            "/engagements/{engagement_id}/runs/{run_id}",
            lambda w: {"engagement_id": w.engagement_id, "run_id": w.run_id},
        ),
        (
            "runs_start",
            "POST",
            "/engagements/{engagement_id}/runs/{run_id}/start",
            lambda w: {"engagement_id": w.engagement_id, "run_id": w.run_id},
        ),
    ],
)
def test_firm_b_denied_on_firm_a_resources(
    isolation_world, case_id, method, path_template, kwargs_builder
):
    del case_id
    w = isolation_world
    built = kwargs_builder(w)
    path = path_template.format(**{k: v for k, v in built.items() if k not in ("json", "params", "files", "data")})
    request_kwargs = {
        "headers": w.headers_b,
    }
    for key in ("json", "params", "files", "data"):
        if key in built:
            request_kwargs[key] = built[key]

    response = client.request(method, path, **request_kwargs)
    _assert_denied(response)


@requires_db
@pytest.mark.parametrize("module_code", MODULE_CODES)
@pytest.mark.parametrize(
    "suffix,method,needs_file",
    [
        ("upload", "POST", True),
        ("run-rules", "POST", False),
        ("run-risk", "POST", False),
        ("risk-scores", "GET", False),
        ("findings", "GET", False),
        ("generate-findings", "POST", False),
        ("reports", "GET", False),
    ],
)
def test_generic_module_endpoints_deny_cross_tenant(
    isolation_world, module_code, suffix, method, needs_file
):
    w = isolation_world
    project_key = {
        "JOURNAL_ENTRY_TESTING": "journal_testing",
        "REVENUE_TESTING": "revenue_testing",
        "PROCUREMENT_TESTING": "procurement_testing",
    }[module_code]
    path = f"/modules/{module_code}/{suffix}"
    kwargs: dict = {
        "headers": w.headers_b,
        "params": {"project_id": w.projects[project_key]},
    }
    if needs_file:
        payload = {
            "JOURNAL_ENTRY_TESTING": (_journal_xlsx(), "journal.xlsx"),
            "REVENUE_TESTING": (_revenue_xlsx(), "revenue.xlsx"),
            "PROCUREMENT_TESTING": (_procurement_xlsx(), "procurement.xlsx"),
        }[module_code]
        kwargs["files"] = {
            "file": (
                payload[1],
                payload[0],
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
    response = client.request(method, path, **kwargs)
    _assert_denied(response)


@requires_db
@pytest.mark.parametrize("module_code", MODULE_CODES)
def test_generic_module_report_download_denies_cross_tenant(isolation_world, module_code):
    w = isolation_world
    response = client.get(
        f"/modules/{module_code}/reports/{w.report_id}/download",
        headers=w.headers_b,
    )
    _assert_denied(response)


# ---------------------------------------------------------------------------
# List endpoints must not leak Firm A records to Firm B
# ---------------------------------------------------------------------------


@requires_db
def test_clients_list_does_not_leak_firm_a(isolation_world):
    w = isolation_world
    response = client.get("/clients", headers=w.headers_b)
    assert response.status_code == 200
    ids = {str(row["id"]) for row in response.json()}
    assert w.client_id not in ids


@requires_db
def test_engagements_list_does_not_leak_firm_a(isolation_world):
    w = isolation_world
    response = client.get("/engagements", headers=w.headers_b)
    assert response.status_code == 200
    ids = {str(row["id"]) for row in response.json()}
    assert w.engagement_id not in ids


@requires_db
def test_projects_list_does_not_leak_firm_a(isolation_world):
    w = isolation_world
    response = client.get("/projects", headers=w.headers_b)
    assert response.status_code == 200
    ids = {str(row["id"]) for row in response.json()}
    for pid in w.projects.values():
        assert pid not in ids


@requires_db
def test_audit_logs_list_does_not_leak_firm_a(isolation_world):
    w = isolation_world
    response = client.get("/audit-logs/me", headers=w.headers_b)
    assert response.status_code == 200
    for row in response.json():
        details = row.get("details") or {}
        assert details.get("marker") != w.marker
        if row.get("entity_id"):
            assert str(row["entity_id"]) != w.audit_log_entity_id or row.get(
                "organization_id"
            ) != str(w.org_a)


@requires_db
def test_firm_a_can_still_read_own_resources(isolation_world):
    """Sanity: isolation denials are not false negatives from broken auth."""
    w = isolation_world
    ok = client.get(f"/engagements/{w.engagement_id}", headers=w.headers_a)
    assert ok.status_code == 200
    ok2 = client.get(f"/findings/{w.finding_id}", headers=w.headers_a)
    assert ok2.status_code == 200
    ok3 = client.get(
        "/rule-results",
        headers=w.headers_a,
        params={"project_id": w.projects["journal_testing"]},
    )
    assert ok3.status_code == 200
    body = ok3.json()
    results = body if isinstance(body, list) else body.get("results", body.get("items", []))
    assert any(str(r.get("id", "")) == w.rule_result_id for r in results) or len(results) >= 1
