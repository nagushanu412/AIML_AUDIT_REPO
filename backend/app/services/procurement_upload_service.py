from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.models.audit import AuditProject, ProcurementInvoice
from app.services.procurement_validator import normalize_procurement_dataframe


def save_procurement_invoices(db: Session, project: AuditProject, df: pd.DataFrame) -> int:
    db.query(ProcurementInvoice).filter(ProcurementInvoice.project_id == project.id).delete()
    normalized = normalize_procurement_dataframe(df)
    models = [
        ProcurementInvoice(
            project_id=project.id,
            invoice_no=str(row["Invoice_No"]),
            invoice_date=row["Invoice_Date"],
            vendor_name=str(row["Vendor_Name"]),
            vendor_gstin=str(row["Vendor_GSTIN"]) or None,
            po_number=str(row["PO_Number"]) or None,
            taxable_amount=row["Taxable_Amount"],
            gst_amount=row["GST_Amount"],
            total_amount=row["Total_Amount"],
            payment_status=str(row["Payment_Status"]) or None,
            reference_no=str(row["Reference_No"]) or None,
        )
        for _, row in normalized.iterrows()
    ]
    db.add_all(models)
    project.total_entries = len(models)
    db.commit()
    return len(models)
