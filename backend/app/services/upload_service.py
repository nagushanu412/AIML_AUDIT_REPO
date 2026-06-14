from __future__ import annotations

from decimal import Decimal

import pandas as pd
from sqlalchemy.orm import Session

from app.models.audit import AuditProject, JournalEntry
from app.services.excel_validator import normalize_dataframe


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
