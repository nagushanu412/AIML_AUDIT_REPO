"""Remediation M2 follow-up Part A — evidence links at finding creation.

End-to-end: upload → run-rules → run-risk → generate-findings for all three
modules, then the same sequence again on the same project. Both runs must
succeed (second run previously failed EvidenceGateViolation).
"""

from __future__ import annotations

import io
import uuid

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import SessionLocal, validate_database_connection
from app.main import app
from app.models.audit import AuditFinding, EvidenceLink
from app.models.organization_id_events import register_organization_id_listeners

register_organization_id_listeners()

client = TestClient(app)

# (label, project_type, upload_path, run_rules, run_risk, generate_findings)
MODULE_FLOWS = (
    (
        "journal",
        "journal_testing",
        "/upload",
        "/run-rules",
        "/run-risk",
        "/generate-findings",
    ),
    (
        "revenue",
        "revenue_testing",
        "/revenue/upload",
        "/revenue/run-rules",
        "/revenue/run-risk",
        "/revenue/generate-findings",
    ),
    (
        "procurement",
        "procurement_testing",
        "/procurement/upload",
        "/procurement/run-rules",
        "/procurement/run-risk",
        "/procurement/generate-findings",
    ),
)


def _db_available() -> bool:
    try:
        validate_database_connection()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not available")


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _xlsx(rows: list[dict]) -> bytes:
    buf = io.BytesIO()
    pd.DataFrame(rows).to_excel(buf, index=False)
    return buf.getvalue()


def _journal_xlsx() -> bytes:
    # Amount above engagement large_value_threshold (100000) → LARGE_VALUE
    return _xlsx(
        [
            {
                "Journal_ID": "EV-J1",
                "Posting_Date": "2026-04-01",
                "Account_Code": "1000",
                "Account_Name": "Cash",
                "Amount": 150000,
                "Debit_Credit": "Debit",
                "User_ID": "auditor1",
                "Description": "evidence-gate e2e seed",
            }
        ]
    )


def _revenue_xlsx() -> bytes:
    # Round total → REV_ROUND_AMOUNT
    return _xlsx(
        [
            {
                "Invoice_No": "INV-EV-1",
                "Invoice_Date": "2026-04-01",
                "Customer_Name": "Acme",
                "Taxable_Amount": 10000,
                "GST_Amount": 1800,
                "Total_Amount": 11800,
            },
            {
                "Invoice_No": "INV-EV-2",
                "Invoice_Date": "2026-04-02",
                "Customer_Name": "Acme",
                "Taxable_Amount": 100000,
                "GST_Amount": 18000,
                "Total_Amount": 118000,
            },
        ]
    )


def _procurement_xlsx() -> bytes:
    # High total, no PO → PROC_MISSING_PO; round total also helps
    return _xlsx(
        [
            {
                "Invoice_No": "PINV-EV-1",
                "Invoice_Date": "2026-04-01",
                "Vendor_Name": "VendorCo",
                "Taxable_Amount": 100000,
                "GST_Amount": 18000,
                "Total_Amount": 118000,
            }
        ]
    )


def _file_bytes(label: str) -> bytes:
    if label == "journal":
        return _journal_xlsx()
    if label == "revenue":
        return _revenue_xlsx()
    return _procurement_xlsx()


def _assert_all_findings_have_evidence(db: Session, project_id: str) -> int:
    findings = (
        db.query(AuditFinding).filter(AuditFinding.project_id == uuid.UUID(project_id)).all()
    )
    assert findings, f"expected findings for project {project_id}"
    for finding in findings:
        n = (
            db.query(EvidenceLink)
            .filter(EvidenceLink.finding_id == finding.id)
            .count()
        )
        assert n >= 1, f"finding {finding.id} has no evidence_links"
    return len(findings)


def _run_analysis_sequence(
    *,
    headers: dict[str, str],
    project_id: str,
    label: str,
    upload_path: str,
    rules_path: str,
    risk_path: str,
    findings_path: str,
    run_label: str,
) -> None:
    up = client.post(
        upload_path,
        headers=headers,
        params={"project_id": project_id},
        files={
            "file": (
                f"{label}.xlsx",
                _file_bytes(label),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert up.status_code == 200, f"{run_label} upload: {up.status_code} {up.text[:400]}"

    rules = client.post(
        rules_path, headers=headers, params={"project_id": project_id}
    )
    assert rules.status_code == 200, (
        f"{run_label} run-rules: {rules.status_code} {rules.text[:400]}"
    )

    risk = client.post(risk_path, headers=headers, params={"project_id": project_id})
    assert risk.status_code == 200, (
        f"{run_label} run-risk: {risk.status_code} {risk.text[:400]}"
    )

    findings = client.post(
        findings_path, headers=headers, params={"project_id": project_id}
    )
    assert findings.status_code == 200, (
        f"{run_label} generate-findings: {findings.status_code} {findings.text[:400]}"
    )
    body = findings.json()
    assert isinstance(body, list)
    assert len(body) >= 1, f"{run_label} expected at least one finding"


@requires_db
@pytest.mark.parametrize(
    "label,project_type,upload_path,rules_path,risk_path,findings_path",
    MODULE_FLOWS,
)
def test_analysis_sequence_twice_with_evidence_links(
    label: str,
    project_type: str,
    upload_path: str,
    rules_path: str,
    risk_path: str,
    findings_path: str,
):
    suffix = uuid.uuid4().hex[:10]
    reg = client.post(
        "/auth/register",
        json={
            "email": f"ev-gate-{label}-{suffix}@example.com",
            "password": "EvidenceGate2026!",
            "full_name": "Evidence Gate Tester",
            "company_name": f"Evidence Gate Firm {suffix}",
        },
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    headers = _auth(token)

    c_resp = client.post(
        "/clients",
        headers=headers,
        json={"name": f"Client {suffix}", "industry": "Manufacturing"},
    )
    assert c_resp.status_code == 201, c_resp.text
    client_id = c_resp.json()["id"]

    e_resp = client.post(
        "/engagements",
        headers=headers,
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

    p_resp = client.post(
        "/projects",
        headers=headers,
        json={
            "engagement_id": engagement_id,
            "name": f"{label} evidence e2e",
            "project_type": project_type,
            "status": "active",
        },
    )
    assert p_resp.status_code == 201, p_resp.text
    project_id = p_resp.json()["id"]

    _run_analysis_sequence(
        headers=headers,
        project_id=project_id,
        label=label,
        upload_path=upload_path,
        rules_path=rules_path,
        risk_path=risk_path,
        findings_path=findings_path,
        run_label=f"{label} first run",
    )

    db = SessionLocal()
    try:
        n1 = _assert_all_findings_have_evidence(db, project_id)
    finally:
        db.close()

    # Same project, full sequence again — run-risk must not 500 on existing findings.
    _run_analysis_sequence(
        headers=headers,
        project_id=project_id,
        label=label,
        upload_path=upload_path,
        rules_path=rules_path,
        risk_path=risk_path,
        findings_path=findings_path,
        run_label=f"{label} second run",
    )

    db = SessionLocal()
    try:
        n2 = _assert_all_findings_have_evidence(db, project_id)
        assert n2 >= 1
        assert n1 >= 1
    finally:
        db.close()
