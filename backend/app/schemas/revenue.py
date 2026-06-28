from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.upload import ValidationResult


class RevenueUploadResponse(BaseModel):
    project_id: UUID
    validation: ValidationResult
    invoices_imported: int
    total_taxable: float = 0
    total_gst: float = 0
    total_revenue: float = 0
    message: str


class RevenueRunRulesResponse(BaseModel):
    project_id: UUID
    total_invoices_analyzed: int
    total_violations_found: int
    violations_by_rule: dict[str, int]
    rule_summary: list[dict]
    message: str


class RevenueRunRiskResponse(BaseModel):
    project_id: UUID
    total_invoices_scored: int
    high_risk: int
    medium_risk: int
    low_risk: int
    message: str


class RevenueRiskScoreOut(BaseModel):
    id: UUID
    revenue_invoice_id: UUID
    total_score: int
    risk_category: str
    rule_breakdown: dict
    invoice_no: str
    invoice_date: str | None = None
    customer_name: str
    total_amount: float
    gst_amount: float
    payment_status: str | None = None
