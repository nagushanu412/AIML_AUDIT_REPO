from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pandas as pd
from sqlalchemy.orm import Session

from app.models.audit import AuditProject, JournalEntry, User
from app.services.excel_validator import normalize_dataframe


def get_or_create_default_project(db: Session) -> AuditProject:
    project = db.query(AuditProject).order_by(AuditProject.created_at).first()
    if project:
        return project

    user = db.query(User).first()
    if not user:
        user = User(
            email="auditor@demo.auditai.com",
            password_hash="pending",
            full_name="Demo Auditor",
            role="auditor",
        )
        db.add(user)
        db.flush()

    project = AuditProject(
        name="Default Journal Entry Audit",
        client_name="Default Client",
        financial_year_end=date(2025, 3, 31),
        large_value_threshold=Decimal("100000.00"),
        user_id=user.id,
    )
    db.add(project)
    db.flush()
    return project


def resolve_project(db: Session, project_id: uuid.UUID | None) -> AuditProject:
    if project_id:
        project = db.query(AuditProject).filter(AuditProject.id == project_id).first()
        if not project:
            raise ValueError(f"Audit project not found: {project_id}")
        return project
    return get_or_create_default_project(db)


def save_journal_entries(
    db: Session,
    project: AuditProject,
    df: pd.DataFrame,
) -> int:
    normalized = normalize_dataframe(df)

    db.query(JournalEntry).filter(JournalEntry.project_id == project.id).delete()

    entries: list[JournalEntry] = []
    for _, row in normalized.iterrows():
        entries.append(
            JournalEntry(
                project_id=project.id,
                journal_id=str(row["Journal_ID"]),
                posting_date=row["Posting_Date"],
                account_code=str(row["Account_Code"]),
                account_name=str(row["Account_Name"]),
                amount=Decimal(str(row["Amount"])),
                debit_credit=str(row["Debit_Credit"]),
                user_id=str(row["User_ID"]),
                description=str(row["Description"]) or None,
            )
        )

    db.add_all(entries)
    project.total_entries = len(entries)
    db.commit()
    return len(entries)
