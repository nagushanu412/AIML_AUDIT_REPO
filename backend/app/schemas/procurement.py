from uuid import UUID

from pydantic import BaseModel

from app.schemas.upload import ValidationResult


class ProcurementUploadResponse(BaseModel):
    project_id: UUID
    validation: ValidationResult
    invoices_imported: int
    total_taxable: float = 0
    total_gst: float = 0
    total_spend: float = 0
    message: str


class ProcurementRunRulesResponse(BaseModel):
    project_id: UUID
    total_invoices_analyzed: int
    total_violations_found: int
    violations_by_rule: dict[str, int]
    rule_summary: list[dict]
    message: str


class ProcurementRunRiskResponse(BaseModel):
    project_id: UUID
    total_invoices_scored: int
    high_risk: int
    medium_risk: int
    low_risk: int
    message: str


class ProcurementRiskScoreOut(BaseModel):
    id: UUID
    procurement_invoice_id: UUID
    total_score: int
    risk_category: str
    rule_breakdown: dict
    invoice_no: str
    invoice_date: str | None = None
    vendor_name: str
    po_number: str | None = None
    total_amount: float
    gst_amount: float
    payment_status: str | None = None
