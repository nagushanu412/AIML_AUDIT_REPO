import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="auditor")
    company_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    clients: Mapped[list["Client"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100))
    gstin: Mapped[str | None] = mapped_column(String(50))
    pan: Mapped[str | None] = mapped_column(String(20))
    contact_person: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="clients")
    engagements: Mapped[list["AuditEngagement"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )


class AuditEngagement(Base):
    __tablename__ = "audit_engagements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    financial_year: Mapped[str] = mapped_column(String(20), nullable=False)
    audit_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Statutory")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="planned")
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    financial_year_end: Mapped[date] = mapped_column(Date, nullable=False)
    large_value_threshold: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("100000.00")
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    client: Mapped["Client"] = relationship(back_populates="engagements")
    projects: Mapped[list["AuditProject"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan"
    )


class AuditProject(Base):
    __tablename__ = "audit_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    engagement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_engagements.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_type: Mapped[str] = mapped_column(String(100), nullable=False, default="journal_testing")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    total_entries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    engagement: Mapped["AuditEngagement"] = relationship(back_populates="projects")
    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    rule_results: Mapped[list["RuleResult"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    risk_scores: Mapped[list["RiskScore"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    audit_findings: Mapped[list["AuditFinding"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    revenue_invoices: Mapped[list["RevenueInvoice"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    revenue_rule_results: Mapped[list["RevenueRuleResult"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    revenue_risk_scores: Mapped[list["RevenueRiskScore"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    procurement_invoices: Mapped[list["ProcurementInvoice"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    procurement_rule_results: Mapped[list["ProcurementRuleResult"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    procurement_risk_scores: Mapped[list["ProcurementRiskScore"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    journal_id: Mapped[str] = mapped_column(String(100), nullable=False)
    posting_date: Mapped[date] = mapped_column(Date, nullable=False)
    account_code: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    debit_credit: Mapped[str] = mapped_column(String(10), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="journal_entries")
    rule_results: Mapped[list["RuleResult"]] = relationship(
        back_populates="journal_entry", cascade="all, delete-orphan"
    )
    risk_score: Mapped["RiskScore | None"] = relationship(
        back_populates="journal_entry", uselist=False, cascade="all, delete-orphan"
    )


class RuleMaster(Base):
    __tablename__ = "rules_master"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    default_score: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    rule_results: Mapped[list["RuleResult"]] = relationship(back_populates="rule")


class RuleResult(Base):
    __tablename__ = "rule_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rules_master.id", ondelete="SET NULL"), nullable=True
    )
    rule_code: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="rule_results")
    journal_entry: Mapped["JournalEntry"] = relationship(back_populates="rule_results")
    rule: Mapped["RuleMaster | None"] = relationship(back_populates="rule_results")


class RiskScore(Base):
    __tablename__ = "risk_scores"
    __table_args__ = (
        UniqueConstraint("project_id", "journal_entry_id", name="uq_risk_project_entry"),
        CheckConstraint(
            "risk_category IN ('low', 'medium', 'high')", name="ck_risk_category"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False
    )
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_category: Mapped[str] = mapped_column(String(20), nullable=False)
    rule_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="risk_scores")
    journal_entry: Mapped["JournalEntry"] = relationship(back_populates="risk_score")


class AuditFinding(Base):
    __tablename__ = "audit_findings"
    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high')", name="ck_finding_risk_level"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    rule_code: Mapped[str] = mapped_column(String(50), nullable=False)
    finding_title: Mapped[str] = mapped_column(String(255), nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    affected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    journal_entry_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="audit_findings")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text)
    generated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ready")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="reports")


class RevenueInvoice(Base):
    __tablename__ = "revenue_invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    invoice_no: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_gstin: Mapped[str | None] = mapped_column(String(50))
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    payment_status: Mapped[str | None] = mapped_column(String(50))
    reference_no: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="revenue_invoices")
    rule_results: Mapped[list["RevenueRuleResult"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    risk_score: Mapped["RevenueRiskScore | None"] = relationship(
        back_populates="invoice", uselist=False, cascade="all, delete-orphan"
    )


class RevenueRuleResult(Base):
    __tablename__ = "revenue_rule_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    revenue_invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("revenue_invoices.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rules_master.id", ondelete="SET NULL"), nullable=True
    )
    rule_code: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="revenue_rule_results")
    invoice: Mapped["RevenueInvoice"] = relationship(back_populates="rule_results")
    rule: Mapped["RuleMaster | None"] = relationship()


class RevenueRiskScore(Base):
    __tablename__ = "revenue_risk_scores"
    __table_args__ = (
        UniqueConstraint("project_id", "revenue_invoice_id", name="uq_revenue_risk_project_invoice"),
        CheckConstraint(
            "risk_category IN ('low', 'medium', 'high')", name="ck_revenue_risk_category"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    revenue_invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("revenue_invoices.id", ondelete="CASCADE"), nullable=False
    )
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_category: Mapped[str] = mapped_column(String(20), nullable=False)
    rule_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="revenue_risk_scores")
    invoice: Mapped["RevenueInvoice"] = relationship(back_populates="risk_score")


class ProcurementInvoice(Base):
    __tablename__ = "procurement_invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    invoice_no: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_gstin: Mapped[str | None] = mapped_column(String(50))
    po_number: Mapped[str | None] = mapped_column(String(100))
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    payment_status: Mapped[str | None] = mapped_column(String(50))
    reference_no: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="procurement_invoices")
    rule_results: Mapped[list["ProcurementRuleResult"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    risk_score: Mapped["ProcurementRiskScore | None"] = relationship(
        back_populates="invoice", uselist=False, cascade="all, delete-orphan"
    )


class ProcurementRuleResult(Base):
    __tablename__ = "procurement_rule_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    procurement_invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("procurement_invoices.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rules_master.id", ondelete="SET NULL"), nullable=True
    )
    rule_code: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="procurement_rule_results")
    invoice: Mapped["ProcurementInvoice"] = relationship(back_populates="rule_results")
    rule: Mapped["RuleMaster | None"] = relationship()


class ProcurementRiskScore(Base):
    __tablename__ = "procurement_risk_scores"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "procurement_invoice_id", name="uq_procurement_risk_project_invoice"
        ),
        CheckConstraint(
            "risk_category IN ('low', 'medium', 'high')", name="ck_procurement_risk_category"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audit_projects.id", ondelete="CASCADE"), nullable=False
    )
    procurement_invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("procurement_invoices.id", ondelete="CASCADE"), nullable=False
    )
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_category: Mapped[str] = mapped_column(String(20), nullable=False)
    rule_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    project: Mapped["AuditProject"] = relationship(back_populates="procurement_risk_scores")
    invoice: Mapped["ProcurementInvoice"] = relationship(back_populates="risk_score")
