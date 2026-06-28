from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pandas as pd

from app.schemas.upload import ValidationErrorItem, ValidationResult
from app.services.revenue_constants import REVENUE_REQUIRED_COLUMNS


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _parse_date(value) -> datetime | None:
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value
    try:
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()
    except Exception:
        return None


def _parse_amount(value) -> Decimal | None:
    if pd.isna(value):
        return None
    try:
        cleaned = str(value).replace(",", "").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def validate_revenue_excel(file_bytes: bytes) -> tuple[ValidationResult, pd.DataFrame | None, float, float, float]:
    errors: list[ValidationErrorItem] = []
    warnings: list[ValidationErrorItem] = []

    try:
        df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    except Exception as exc:
        return (
            ValidationResult(
                is_valid=False,
                total_rows=0,
                errors=[ValidationErrorItem(message=f"Unable to read Excel file: {exc}")],
            ),
            None,
            0.0,
            0.0,
            0.0,
        )

    if df.empty:
        return (
            ValidationResult(
                is_valid=False,
                total_rows=0,
                errors=[ValidationErrorItem(message="Excel file contains no data rows.")],
            ),
            None,
            0.0,
            0.0,
            0.0,
        )

    df = _normalize_columns(df)
    missing = [col for col in REVENUE_REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        return (
            ValidationResult(
                is_valid=False,
                total_rows=len(df),
                errors=[
                    ValidationErrorItem(
                        message=f"Missing required columns: {', '.join(missing)}"
                    )
                ],
            ),
            None,
            0.0,
            0.0,
            0.0,
        )

    total_taxable = Decimal("0")
    total_gst = Decimal("0")
    total_revenue = Decimal("0")

    for idx, row in df.iterrows():
        row_num = int(idx) + 2
        for col in REVENUE_REQUIRED_COLUMNS:
            if pd.isna(row[col]) or str(row[col]).strip() == "":
                errors.append(
                    ValidationErrorItem(
                        row=row_num,
                        column=col,
                        message=f"Blank value in required column '{col}'.",
                    )
                )

        if _parse_date(row["Invoice_Date"]) is None:
            errors.append(
                ValidationErrorItem(
                    row=row_num,
                    column="Invoice_Date",
                    message="Invalid or missing invoice date.",
                )
            )

        taxable = _parse_amount(row["Taxable_Amount"])
        gst = _parse_amount(row["GST_Amount"])
        total = _parse_amount(row["Total_Amount"])

        for col, val in [
            ("Taxable_Amount", taxable),
            ("GST_Amount", gst),
            ("Total_Amount", total),
        ]:
            if val is None:
                errors.append(
                    ValidationErrorItem(
                        row=row_num,
                        column=col,
                        message=f"Invalid or missing {col}.",
                    )
                )

        if taxable is not None and gst is not None and total is not None:
            expected = taxable + gst
            if abs(total - expected) > Decimal("1.00"):
                warnings.append(
                    ValidationErrorItem(
                        row=row_num,
                        column="Total_Amount",
                        message=f"Total ({total}) differs from Taxable + GST ({expected}).",
                    )
                )

    if len(errors) == 0:
        for _, row in df.iterrows():
            taxable = _parse_amount(row["Taxable_Amount"]) or Decimal("0")
            gst = _parse_amount(row["GST_Amount"]) or Decimal("0")
            total = _parse_amount(row["Total_Amount"]) or Decimal("0")
            total_taxable += taxable
            total_gst += gst
            total_revenue += total

    return (
        ValidationResult(
            is_valid=len(errors) == 0,
            total_rows=len(df),
            total_debit=float(total_taxable),
            total_credit=float(total_gst),
            errors=errors,
            warnings=warnings,
        ),
        df if len(errors) == 0 else None,
        float(total_taxable),
        float(total_gst),
        float(total_revenue),
    )


def normalize_revenue_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Invoice_Date"] = pd.to_datetime(
        out["Invoice_Date"], dayfirst=True, errors="coerce"
    ).dt.date
    for col in ("Taxable_Amount", "GST_Amount", "Total_Amount"):
        out[col] = out[col].apply(lambda v: _parse_amount(v) or Decimal("0"))
    out["Invoice_No"] = out["Invoice_No"].astype(str).str.strip()
    out["Customer_Name"] = out["Customer_Name"].astype(str).str.strip()
    if "Customer_GSTIN" in out.columns:
        out["Customer_GSTIN"] = out["Customer_GSTIN"].fillna("").astype(str).str.strip()
    else:
        out["Customer_GSTIN"] = ""
    if "Payment_Status" in out.columns:
        out["Payment_Status"] = out["Payment_Status"].fillna("").astype(str).str.strip()
    else:
        out["Payment_Status"] = ""
    if "Reference_No" in out.columns:
        out["Reference_No"] = out["Reference_No"].fillna("").astype(str).str.strip()
    else:
        out["Reference_No"] = ""
    return out
