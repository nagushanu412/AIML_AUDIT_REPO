from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models.audit import (
    AuditFinding,
    AuditProject,
    ProcurementRiskScore,
    ProcurementRuleResult,
    RevenueRiskScore,
    RevenueRuleResult,
    RiskScore,
    RuleResult,
)

REPORTS_DIR = Path(__file__).resolve().parents[2] / "generated_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _risk_counts(db: Session, project_id: uuid.UUID) -> dict[str, int]:
    return {
        cat: db.query(RiskScore)
        .filter(RiskScore.project_id == project_id, RiskScore.risk_category == cat)
        .count()
        for cat in ("high", "medium", "low")
    }


def _violations_by_rule(db: Session, project_id: uuid.UUID) -> dict[str, int]:
    rows = (
        db.query(RuleResult.rule_code)
        .filter(RuleResult.project_id == project_id, RuleResult.triggered.is_(True))
        .all()
    )
    counts: dict[str, int] = {}
    for (code,) in rows:
        counts[code] = counts.get(code, 0) + 1
    return counts


def _revenue_risk_counts(db: Session, project_id: uuid.UUID) -> dict[str, int]:
    return {
        cat: db.query(RevenueRiskScore)
        .filter(RevenueRiskScore.project_id == project_id, RevenueRiskScore.risk_category == cat)
        .count()
        for cat in ("high", "medium", "low")
    }


def _revenue_violations_by_rule(db: Session, project_id: uuid.UUID) -> dict[str, int]:
    rows = (
        db.query(RevenueRuleResult.rule_code)
        .filter(RevenueRuleResult.project_id == project_id, RevenueRuleResult.triggered.is_(True))
        .all()
    )
    counts: dict[str, int] = {}
    for (code,) in rows:
        counts[code] = counts.get(code, 0) + 1
    return counts


def _build_revenue_summary(db: Session, project: AuditProject) -> dict:
    findings = (
        db.query(AuditFinding)
        .filter(AuditFinding.project_id == project.id)
        .order_by(AuditFinding.created_at.desc())
        .all()
    )
    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "project_type": "revenue_testing",
        "total_entries": project.total_entries,
        "violations": db.query(RevenueRuleResult)
        .filter(RevenueRuleResult.project_id == project.id, RevenueRuleResult.triggered.is_(True))
        .count(),
        "risk_distribution": _revenue_risk_counts(db, project.id),
        "violations_by_rule": _revenue_violations_by_rule(db, project.id),
        "findings_count": len(findings),
        "findings": [
            {
                "rule_code": f.rule_code,
                "title": f.finding_title,
                "risk_level": f.risk_level,
                "affected_count": f.affected_count,
                "observation": f.observation,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _procurement_risk_counts(db: Session, project_id: uuid.UUID) -> dict[str, int]:
    return {
        cat: db.query(ProcurementRiskScore)
        .filter(ProcurementRiskScore.project_id == project_id, ProcurementRiskScore.risk_category == cat)
        .count()
        for cat in ("high", "medium", "low")
    }


def _procurement_violations_by_rule(db: Session, project_id: uuid.UUID) -> dict[str, int]:
    rows = (
        db.query(ProcurementRuleResult.rule_code)
        .filter(ProcurementRuleResult.project_id == project_id, ProcurementRuleResult.triggered.is_(True))
        .all()
    )
    counts: dict[str, int] = {}
    for (code,) in rows:
        counts[code] = counts.get(code, 0) + 1
    return counts


def _build_procurement_summary(db: Session, project: AuditProject) -> dict:
    findings = (
        db.query(AuditFinding)
        .filter(AuditFinding.project_id == project.id)
        .order_by(AuditFinding.created_at.desc())
        .all()
    )
    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "project_type": "procurement_testing",
        "total_entries": project.total_entries,
        "violations": db.query(ProcurementRuleResult)
        .filter(ProcurementRuleResult.project_id == project.id, ProcurementRuleResult.triggered.is_(True))
        .count(),
        "risk_distribution": _procurement_risk_counts(db, project.id),
        "violations_by_rule": _procurement_violations_by_rule(db, project.id),
        "findings_count": len(findings),
        "findings": [
            {
                "rule_code": f.rule_code,
                "title": f.finding_title,
                "risk_level": f.risk_level,
                "affected_count": f.affected_count,
                "observation": f.observation,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_summary(db: Session, project: AuditProject) -> dict:
    if project.project_type == "revenue_testing":
        return _build_revenue_summary(db, project)
    if project.project_type == "procurement_testing":
        return _build_procurement_summary(db, project)
    findings = (
        db.query(AuditFinding)
        .filter(AuditFinding.project_id == project.id)
        .order_by(AuditFinding.created_at.desc())
        .all()
    )
    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "total_entries": project.total_entries,
        "violations": db.query(RuleResult)
        .filter(RuleResult.project_id == project.id, RuleResult.triggered.is_(True))
        .count(),
        "risk_distribution": _risk_counts(db, project.id),
        "violations_by_rule": _violations_by_rule(db, project.id),
        "findings_count": len(findings),
        "findings": [
            {
                "rule_code": f.rule_code,
                "title": f.finding_title,
                "risk_level": f.risk_level,
                "affected_count": f.affected_count,
                "observation": f.observation,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _write_excel(path: Path, summary: dict) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["AIML Audit Report"])
    ws.append(["Project", summary["project_name"]])
    ws.append(["Total entries", summary["total_entries"]])
    ws.append(["Violations", summary["violations"]])
    ws.append(["High risk", summary["risk_distribution"]["high"]])
    ws.append(["Medium risk", summary["risk_distribution"]["medium"]])
    ws.append(["Low risk", summary["risk_distribution"]["low"]])
    ws.append([])
    ws.append(["Violations by rule"])
    for code, count in summary["violations_by_rule"].items():
        ws.append([code, count])

    ws2 = wb.create_sheet("Findings")
    ws2.append(["Rule", "Title", "Risk", "Count", "Observation", "Recommendation"])
    for f in summary["findings"]:
        ws2.append([
            f["rule_code"],
            f["title"],
            f["risk_level"],
            f["affected_count"],
            f["observation"],
            f["recommendation"],
        ])
    wb.save(path)


def _write_pdf(path: Path, summary: dict) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    lines = [
        "AIML Audit Analytics — Journal Audit Report",
        f"Project: {summary['project_name']}",
        f"Total entries: {summary['total_entries']}",
        f"Rule violations: {summary['violations']}",
        f"High / Medium / Low risk: {summary['risk_distribution']['high']} / "
        f"{summary['risk_distribution']['medium']} / {summary['risk_distribution']['low']}",
        "",
        "Findings summary:",
    ]
    for line in lines:
        c.drawString(2 * cm, y, line[:90])
        y -= 0.6 * cm
    for f in summary["findings"][:12]:
        c.drawString(2 * cm, y, f"- {f['rule_code']}: {f['title']} ({f['affected_count']} entries)"[:95])
        y -= 0.55 * cm
        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
    c.save()


def _write_json(path: Path, summary: dict) -> None:
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def generate_report_file(
    db: Session,
    project: AuditProject,
    report_type: str,
) -> tuple[str, str, dict]:
    """Returns (file_name, absolute_path, metadata)."""
    summary = _build_summary(db, project)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = project.name.replace(" ", "_")

    if report_type in (
        "journal_audit_excel",
        "working_paper",
        "revenue_audit_excel",
        "revenue_working_paper",
        "procurement_audit_excel",
        "procurement_working_paper",
    ):
        ext = "xlsx"
        file_name = f"{safe_name}_{report_type}_{timestamp}.xlsx"
        path = REPORTS_DIR / file_name
        _write_excel(path, summary)
    elif report_type in ("journal_audit_pdf", "revenue_audit_pdf", "procurement_audit_pdf"):
        ext = "pdf"
        file_name = f"{safe_name}_{report_type}_{timestamp}.pdf"
        path = REPORTS_DIR / file_name
        _write_pdf(path, summary)
    else:
        ext = "json"
        file_name = f"{safe_name}_{report_type}_{timestamp}.json"
        path = REPORTS_DIR / file_name
        _write_json(path, summary)

    del ext
    return file_name, str(path), summary
