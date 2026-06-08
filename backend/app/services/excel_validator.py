from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pandas as pd

from app.schemas.upload import ValidationErrorItem, ValidationResult
from app.services.constants import REQUIRED_COLUMNS, VALID_DEBIT_CREDIT


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


def validate_excel(file_bytes: bytes) -> tuple[ValidationResult, pd.DataFrame | None]:
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
        )

    if df.empty:
        return (
            ValidationResult(
                is_valid=False,
                total_rows=0,
                errors=[ValidationErrorItem(message="Excel file contains no data rows.")],
            ),
            None,
        )

    df = _normalize_columns(df)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
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
        )

    for idx, row in df.iterrows():
        row_num = int(idx) + 2
        for col in REQUIRED_COLUMNS:
            if col == "Description":
                continue
            if pd.isna(row[col]) or str(row[col]).strip() == "":
                errors.append(
                    ValidationErrorItem(
                        row=row_num,
                        column=col,
                        message=f"Blank value in required column '{col}'.",
                    )
                )

        if _parse_date(row["Posting_Date"]) is None:
            errors.append(
                ValidationErrorItem(
                    row=row_num,
                    column="Posting_Date",
                    message="Invalid or missing posting date.",
                )
            )

        amount = _parse_amount(row["Amount"])
        if amount is None:
            errors.append(
                ValidationErrorItem(
                    row=row_num,
                    column="Amount",
                    message="Invalid or missing amount.",
                )
            )
        elif amount < 0:
            warnings.append(
                ValidationErrorItem(
                    row=row_num,
                    column="Amount",
                    message="Negative amount detected; absolute value will be stored.",
                )
            )

        dc = str(row["Debit_Credit"]).strip().upper()
        if dc not in VALID_DEBIT_CREDIT:
            errors.append(
                ValidationErrorItem(
                    row=row_num,
                    column="Debit_Credit",
                    message="Debit_Credit must be Debit, Credit, D, or C.",
                )
            )

    return (
        ValidationResult(
            is_valid=len(errors) == 0,
            total_rows=len(df),
            errors=errors,
            warnings=warnings,
        ),
        df if len(errors) == 0 else None,
    )


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Posting_Date"] = pd.to_datetime(
        out["Posting_Date"], dayfirst=True, errors="coerce"
    ).dt.date
    out["Amount"] = out["Amount"].apply(
        lambda v: abs(_parse_amount(v) or Decimal("0"))
    )
    out["Debit_Credit"] = out["Debit_Credit"].apply(
        lambda v: "Debit"
        if str(v).strip().upper() in {"DEBIT", "D"}
        else "Credit"
    )
    out["Journal_ID"] = out["Journal_ID"].astype(str).str.strip()
    out["Account_Code"] = out["Account_Code"].astype(str).str.strip()
    out["Account_Name"] = out["Account_Name"].astype(str).str.strip()
    out["User_ID"] = out["User_ID"].astype(str).str.strip()
    out["Description"] = out["Description"].fillna("").astype(str).str.strip()
    return out
