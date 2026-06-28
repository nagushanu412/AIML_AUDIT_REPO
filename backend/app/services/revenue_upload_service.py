from __future__ import annotations

import uuid

import pandas as pd
from sqlalchemy.orm import Session

from app.models.audit import AuditProject, RevenueInvoice
from app.services.revenue_validator import normalize_revenue_dataframe


def save_revenue_invoices(
    db: Session,
    project: AuditProject,
    df: pd.DataFrame,
) -> int:
    db.query(RevenueInvoice).filter(RevenueInvoice.project_id == project.id).delete()

    normalized = normalize_revenue_dataframe(df)
    models: list[RevenueInvoice] = []

    for _, row in normalized.iterrows():
        models.append(
            RevenueInvoice(
                project_id=project.id,
                invoice_no=str(row["Invoice_No"]),
                invoice_date=row["Invoice_Date"],
                customer_name=str(row["Customer_Name"]),
                customer_gstin=str(row["Customer_GSTIN"]) or None,
                taxable_amount=row["Taxable_Amount"],
                gst_amount=row["GST_Amount"],
                total_amount=row["Total_Amount"],
                payment_status=str(row["Payment_Status"]) or None,
                reference_no=str(row["Reference_No"]) or None,
            )
        )

    db.add_all(models)
    project.total_entries = len(models)
    db.commit()
    return len(models)
