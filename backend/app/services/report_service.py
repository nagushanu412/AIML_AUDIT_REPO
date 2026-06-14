from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditProject, Report
from app.services.report_export import generate_report_file


def generate_project_report(
    db: Session,
    project: AuditProject,
    user_id: uuid.UUID,
    report_type: str = "journal_audit_summary",
) -> Report:
    file_name, file_path, metadata = generate_report_file(db, project, report_type)

    report = Report(
        project_id=project.id,
        report_type=report_type,
        file_name=file_name,
        file_path=file_path,
        generated_by=user_id,
        status="ready",
        metadata_=metadata,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
