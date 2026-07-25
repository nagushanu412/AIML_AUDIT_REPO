# Phase 3 — Technical Design & Execution Plan

**Document type:** Architecture & implementation planning (no code)  
**Date:** July 8, 2026  
**Status:** Design complete — pending stakeholder approval before implementation  
**Prerequisites (stated):** Phase 1 complete, Phase 2 complete, Wave 0 (Project Stabilization) complete

**Related documents:**

- [PHASE3_AI_AND_SCALABILITY.md](./PHASE3_AI_AND_SCALABILITY.md) — high-level roadmap
- [PHASE2_FINAL_IMPLEMENTATION_REPORT.md](./PHASE2_FINAL_IMPLEMENTATION_REPORT.md) — Phase 2 deliverables
- [PHASE3_READINESS_REPORT.md](../status/PHASE3_READINESS_REPORT.md) — pre-Phase 3 audit (reference)

---

## Executive Summary

Phase 3 transforms AIML_AUDIT from a **three-module audit application** into an **enterprise-scale AI audit platform** supporting 22+ modules, thousands of organizations, and firms from solo CAs to Big Four scale.

The accepted architectural decision is:

> **Migrate Journal Entry, Revenue, and Procurement Testing into a Generic Module Framework (GMMF) before building the remaining 19 catalog modules.**

The user-facing experience (22-module grid, 3 Active / 19 Coming Soon, per-module workspaces) **remains unchanged**. Only internal architecture changes.

**Recommended implementation order:** Framework → Migration → Remaining modules → AI → Billing → Enterprise features → Scale.

---

# Part 1 — Generic Module Framework Design (GMMF)

## 1.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GENERIC MODULE PLATFORM                          │
├─────────────────────────────────────────────────────────────────────────┤
│  Generic REST API          Generic Frontend Workspace                    │
│  /api/v2/modules/{code}/*  AuditModuleWorkspace + config-driven panels   │
├─────────────────────────────────────────────────────────────────────────┤
│  Generic Engines (shared)                                                │
│  Upload → Validate → Rules → Risk → Findings → Reports → Analysis Run  │
├─────────────────────────────────────────────────────────────────────────┤
│  Module Registry + Plugin Host                                           │
│  audit_module_catalog + module_plugin_config + ModuleProvider protocol │
├─────────────────────────────────────────────────────────────────────────┤
│  Module Plugins (pluggable)                                              │
│  JournalEntryPlugin | RevenuePlugin | ProcurementPlugin | ... (19+)      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1.2 Plugin Architecture

### Purpose

Allow each audit module to register domain-specific behavior (rules, schemas, templates) without duplicating orchestration code.

### Responsibilities

- Define `ModuleProvider` protocol that every built module implements
- Load plugins at application startup from registry
- Route generic engine calls to the correct plugin by `module_code`
- Support config-only modules (no Python code) for simple rule-based modules at scale

### Public Interface (conceptual)

```python
class ModuleProvider(Protocol):
    code: str                          # e.g. "JOURNAL_ENTRY_TESTING"
    project_type: str                  # e.g. "journal_testing"

    def input_schema(self) -> InputSchema
    def validation_rules(self) -> list[ValidationRule]
    def rule_evaluators(self) -> dict[str, RuleEvaluator]
    def finding_templates(self) -> dict[str, FindingTemplate]
    def report_templates(self) -> list[ReportTemplate]
    def kpi_definitions(self) -> list[KpiDefinition]
    def optional_ui_slots(self) -> list[UiSlot]  # module-specific panels
```

### Dependencies

- `ModuleRegistry` (loads from DB + Python entry points)
- Generic engines (call plugin methods)
- `TenantContext`, `project_access` (tenant isolation)
- `RuleMaster` table (shared rule config store)

### Future Extensibility

- Third-party plugins via Python entry points (`pyproject.toml` `[project.entry-points."aiml.modules"]`)
- Config-only modules stored as JSON in `module_plugin_config`
- Hot-reload in development; versioned plugin bundles in production
- Module SDK for partner-built custom modules (marketplace vision)

---

## 1.3 Module Registry

### Purpose

Single source of truth for which modules exist, their status, and how to invoke them.

### Responsibilities

- Extend existing `audit_module_catalog` (22 modules seeded)
- Map `module_code` ↔ `project_type` ↔ `slug` ↔ plugin class
- Enforce subscription plan `enabled_module_codes`
- Track `implementation_status` (built, beta, planned)
- Resolve plugin at runtime

### Public Interface

| Method | Description |
|--------|-------------|
| `get_module(code)` | Return catalog row + plugin config |
| `list_modules(tenant)` | Filter by plan + org |
| `resolve_provider(code)` | Return `ModuleProvider` instance |
| `is_enabled(engagement_id, code)` | Check `engagement_enabled_modules` |

### Dependencies

- `audit_module_catalog` (existing)
- `module_plugin_config` (new)
- `engagement_enabled_modules` (existing)
- `SubscriptionRepository` (plan gating)

### Future Extensibility

- Module versioning (`module_version` column)
- Beta flags per organization
- Regional compliance packs (IND AS, IFRS) as module bundles

---

## 1.4 Module Metadata

### Purpose

Describe each module for catalog UI, API discovery, and workspace rendering without hardcoded frontend lists.

### Responsibilities

Store in `audit_module_catalog` (existing) + extend with:

| Field | Example |
|-------|---------|
| `code` | `REVENUE_TESTING` |
| `name` | Revenue Testing |
| `slug` | `revenue-testing` |
| `category` | Revenue |
| `icon` | Receipt |
| `implementation_status` | built / beta / planned |
| `project_type` | revenue_testing |
| `display_order` | 2 |
| `input_format` | xlsx |
| `required_columns` | JSON array |
| `rule_prefix` | REV_ |
| `primary_entity_label` | Invoice |
| `theme_color` | indigo |

### Public Interface

- `GET /api/v2/modules/catalog` — returns full metadata for grid
- `GET /api/v2/modules/{code}/metadata` — workspace bootstrap payload

### Dependencies

- Alembic migration extending `audit_module_catalog` columns (additive)
- Seed script updates for 22 modules

### Future Extensibility

- i18n labels
- Firm-custom module descriptions
- Module dependency graph (e.g. Procurement requires PO Matching)

---

## 1.5 Module Configuration

### Purpose

Store per-module behavioral config separately from code so new modules can be mostly data-driven.

### Responsibilities

New table `module_plugin_config`:

```json
{
  "module_code": "REVENUE_TESTING",
  "input_schema": { "columns": [...], "required": [...] },
  "validation": { "rules": [...] },
  "rule_codes": ["REV_DUPLICATE_INVOICE", "REV_CUTOFF", ...],
  "finding_templates": { "REV_CUTOFF": { "title": "...", ... } },
  "report_types": ["revenue_audit_excel", "revenue_audit_pdf"],
  "kpi_cards": ["high_risk_invoices", "gst_mismatch_count"],
  "risk_thresholds": { "high": 40, "medium": 20 },
  "ui_config": { "stepper_steps": 6, "accent": "indigo" }
}
```

### Public Interface

- Loaded by `ModuleRegistry.resolve_provider()`
- Admin API (Phase 3 M7): read-only for firms; editable for platform admin

### Dependencies

- `module_plugin_config` table
- Migration seeds from existing `*_constants.py` files

### Future Extensibility

- Firm-level overrides (`organization_module_config`)
- A/B test rule thresholds per engagement

---

## 1.6 Generic Upload Engine

### Purpose

Single upload pipeline for all modules: accept file, validate format, persist records, update project stats.

### Responsibilities

- Accept `multipart/form-data` file + `project_id`
- Delegate column/schema validation to plugin `input_schema()`
- Persist via plugin's `record_repository` adapter
- Enforce file size limits from subscription plan
- Write `usage_records` (upload count, bytes)
- Respect analysis run lock (immutable when run is locked)

### Public Interface

```
POST /api/v2/modules/{code}/upload?project_id={uuid}
→ UploadResult { total_records, validation, warnings }
```

Internal:

```python
class UploadEngine:
    def upload(self, db, tenant, project_id, file, provider: ModuleProvider) -> UploadResult
```

### Dependencies

- `BlobStorageAdapter` (evidence already uses; extend for temp upload staging if needed)
- `ValidationEngine`
- Plugin record persistence adapter
- `run_lock_guard` (wire to upload — currently partial)

### Future Extensibility

- Direct ERP connectors (Tally, SAP) bypassing file upload
- Chunked upload for 100k+ row files
- Virus scan hook

---

## 1.7 Generic Validation Engine

### Purpose

Validate uploaded data against module-specific schemas and cross-field rules before analysis.

### Responsibilities

- Column presence and type coercion
- Row-level validation (amounts, dates, GST arithmetic)
- Aggregate validation (debit/credit balance for journal)
- Return standardized `ValidationResult` (existing schema in `schemas/upload.py`)

### Public Interface

```python
class ValidationEngine:
    def validate(self, df, provider: ModuleProvider, engagement: AuditEngagement) -> ValidationResult
```

### Dependencies

- Plugin `input_schema()` and `validation_rules()`
- Shared helpers extracted from current `excel_validator.py`, `revenue_validator.py`, `procurement_validator.py`
- Pandas / openpyxl (existing)

### Future Extensibility

- Custom validators registered per plugin
- Async validation for large files via worker queue

---

## 1.8 Generic Rule Engine

### Purpose

Execute audit rules against persisted records and write rule results.

### Responsibilities

- Load active rules from `rules_master` filtered by module prefix
- Merge `RuleMaster.config_schema` with plugin defaults
- Invoke plugin-registered `RuleEvaluator` per `rule_code`
- Write results to generic `module_rule_results` (new) or plugin-specific tables during migration
- Return `rule_summary` (violations count per rule)

### Public Interface

```
POST /api/v2/modules/{code}/run-rules?project_id={uuid}
→ RunRulesResult { rule_summary, total_violations }
```

Internal:

```python
class RuleEngine:
    def run(self, db, project_id, provider: ModuleProvider) -> RunRulesResult
```

### Dependencies

- `RuleMaster` (existing)
- Plugin `rule_evaluators()`
- `RuleResult` persistence adapter

### Future Extensibility

- Rule chaining (rule A triggers rule B)
- ML-assisted rules (Phase 3 M4) as optional evaluator type
- Rule simulation / dry-run mode

---

## 1.9 Generic Risk Engine

### Purpose

Aggregate rule violation scores into per-entity risk categories.

### Responsibilities

- Read rule results for project
- Apply weighted scoring from `RuleMaster.default_score`
- Categorize high/medium/low (thresholds from plugin config, default 40/20)
- Persist `module_risk_scores` (new generic table or adapter)
- Return risk distribution summary

### Public Interface

```
POST /api/v2/modules/{code}/run-risk?project_id={uuid}
GET  /api/v2/modules/{code}/risk-scores?project_id={uuid}
```

### Dependencies

- `RuleEngine` output
- Plugin `risk_thresholds` config
- Single `_category()` implementation (replace 3 copies)

### Future Extensibility

- Engagement-level materiality integration (Phase 3 M8)
- Custom risk models per firm

---

## 1.10 Generic Findings Engine

### Purpose

Group rule violations into audit findings with standard lifecycle fields.

### Responsibilities

- Group violations by `rule_code`
- Apply plugin `finding_templates()` for title, observation, impact, recommendation
- Compute `risk_level` from violation count × rule score
- Write to shared `audit_findings` table (existing)
- Set initial `status = open`, `remediation_status = not_started`
- Link to `project_id` and optionally `module_analysis_run_id`

### Public Interface

```
POST /api/v2/modules/{code}/generate-findings?project_id={uuid}
GET  /api/v2/modules/{code}/findings?project_id={uuid}
```

Engagement-wide (existing, keep):

```
GET /engagements/{id}/findings  (cross-module, with module_name badge)
```

### Dependencies

- `audit_findings` (existing)
- `FindingLifecycleService` (existing)
- Plugin finding templates

### Future Extensibility

- Cross-module finding relationships (Phase 2 extension)
- AI-generated narrative overlay (Phase 3 M4) with human approval

---

## 1.11 Generic Report Engine

### Purpose

Generate exportable audit reports from project analysis results.

### Responsibilities

- Build summary from plugin KPI definitions + findings + risk scores
- Generate Excel, PDF, JSON, working paper formats
- Store file via `BlobStorageAdapter`
- Write `reports` + `report_history` rows
- Enforce `max_reports` from subscription plan

### Public Interface

```
POST /api/v2/modules/{code}/reports/generate?project_id={uuid}&report_type={type}
GET  /api/v2/modules/{code}/reports?project_id={uuid}
GET  /api/v2/reports/{id}/download
```

### Dependencies

- `report_export.py` refactored into template registry
- `ReportService` (existing)
- Plugin `report_templates()`

### Future Extensibility

- Firm-branded templates (`report_templates` table)
- Scheduled report generation

---

## 1.12 Generic Analysis Engine

### Purpose

Orchestrate the full module pipeline as a single atomic analysis run — the Phase 2 `ModuleAnalysisRun` becomes the real execution unit.

### Responsibilities

- States: `draft` → `queued` → `running` → `completed` | `failed` | `locked` | `archived`
- Execute pipeline: upload (optional) → validate → rules → risk → findings
- Track progress percentage and step labels
- Support **Official Run** designation (immutable after lock)
- Enforce `run_lock_guard` on all mutations when locked
- Queue long-running jobs via Redis worker (Phase 3 M1 infra)

### Public Interface

```
POST /engagements/{id}/runs                    # create draft
POST /engagements/{id}/runs/{run_id}/start     # queue execution
GET  /engagements/{id}/runs/{run_id}           # status + progress
POST /engagements/{id}/runs/{run_id}/lock      # official run
```

Internal:

```python
class AnalysisEngine:
    def execute_run(self, db, run_id: UUID) -> None  # worker task
```

### Dependencies

- All generic engines above
- `AnalysisRunService` (existing, extend worker)
- Redis + Celery/RQ (Phase 3 M1)
- `EngagementHubService` (existing)

### Future Extensibility

- Parallel step execution where independent
- Partial re-run (rules only, skip upload)
- Run comparison (diff between two official runs)

---

## 1.13 Generic REST API

### Purpose

Unified API surface for all modules, versioned, tenant-scoped, plan-gated.

### Responsibilities

- Prefix: `/api/v2/modules/{module_code}/`
- Standard resource paths across all modules
- Deprecation headers on legacy paths (`/upload`, `/revenue/*`, `/procurement/*`)
- OpenAPI 3.1 spec auto-generated
- Rate limiting per `subscription_plans.api_rate_limit`

### Standard Endpoints (all modules)

| Method | Path | Action |
|--------|------|--------|
| GET | `/metadata` | Module config for workspace |
| POST | `/upload` | Upload input file |
| POST | `/run-rules` | Execute rules |
| POST | `/run-risk` | Score risk |
| GET | `/risk-scores` | List risk scores |
| POST | `/generate-findings` | Create findings |
| GET | `/findings` | List findings |
| POST | `/reports/generate` | Generate report |
| GET | `/reports` | List reports |

### Cross-cutting (unchanged)

- `/engagements/{id}/team/*`
- `/engagements/{id}/evidence/*`
- `/engagements/{id}/findings` (engagement-wide)
- `/engagements/{id}/runs/*`
- `/engagements/{id}/hub`
- `/modules/catalog`

### Dependencies

- FastAPI router factory: `create_module_router(provider)`
- API versioning middleware
- `TenantContext` on all routes

### Future Extensibility

- GraphQL facade for executive dashboard
- Webhook callbacks on run completion

---

## 1.14 Generic Frontend Workspace

### Purpose

One workspace shell that renders any module from metadata + config, preserving current per-module look-and-feel.

### Responsibilities

- Bootstrap from `GET /api/v2/modules/{code}/metadata`
- Render standard sections via config:
  1. Module header (title, description, icon, accent color)
  2. Client + engagement picker (shared `ClientEngagementSection`)
  3. Project selection (filter by `project_type`)
  4. File upload (columns hint from metadata)
  5. Validation panel
  6. Analysis section (rule list from metadata)
  7. Results summary KPI cards
  8. Audit findings panel (shared)
  9. Line-level findings table (plugin slot OR generic table from config)
  10. Export section
  11. Workflow stepper (optional, from `ui_config`)
- Load module-specific panel via dynamic slot (e.g. `JournalLineTable`, `InvoiceRegister`)

### Public Interface (React)

```tsx
<AuditModuleWorkspace moduleCode="REVENUE_TESTING" />
```

Route strategy:

- Dedicated routes preserved: `/dashboard/ai-modules/revenue-testing` → renders `<AuditModuleWorkspace moduleCode="REVENUE_TESTING" />`
- `[slug]` route: active modules with dedicated pages redirect; planned modules show Coming Soon

### Dependencies

- `lib/api` generic module client functions
- Shared components from `components/journal-entry-testing/` (promoted to `components/module-workspace/`)
- Module config JSON from API

### Future Extensibility

- Plugin UI bundles (federated modules)
- Embedded AI copilot panel (Phase 3 M4)

---

## 1.15 Dynamic Routing

### Purpose

Route users to correct workspace without maintaining 22 separate page files.

### Strategy

| Route | Behavior |
|-------|----------|
| `/dashboard/ai-modules` | Catalog grid (unchanged) |
| `/dashboard/ai-modules/{slug}` | Resolve slug → `module_code`; if `built`, render `AuditModuleWorkspace`; if `planned`, show Coming Soon card |
| Legacy dedicated routes | Keep as aliases during migration (no user-visible change) |

### Implementation

- `catalogUtils.hrefForModuleSlug()` extended to always route built modules through workspace
- Next.js middleware: auth gate on `/dashboard/*` (Wave 0 deliverable)
- Slug → code resolution from API catalog (not hardcoded `modules.ts`)

### Dependencies

- Module catalog API
- `AuditModuleWorkspace`

---

## 1.16 Module Lifecycle

```
Catalog (planned)
    ↓ platform enables implementation_status = beta
Beta (pilot firms via feature flag)
    ↓ acceptance tests pass
Built (available per subscription plan)
    ↓ engagement enable
Engagement Enabled
    ↓ auto-provision
Project + Draft Analysis Run (Auto Workspace)
    ↓ user uploads + runs
Completed Analysis Run
    ↓ partner designates
Official Run (locked, immutable)
    ↓ engagement closes
Archived (read-only, retention policy)
```

### State Owners

| State | Table / Service |
|-------|-----------------|
| Catalog status | `audit_module_catalog.implementation_status` |
| Engagement enable | `engagement_enabled_modules` |
| Project | `audit_projects` |
| Analysis run | `module_analysis_runs` |
| Findings | `audit_findings` + lifecycle |
| Official lock | `module_analysis_runs.is_official`, `locked_at` |

---

# Part 2 — Existing Module Migration Strategy

## 2.1 Migration Principles

1. **Strangler fig pattern** — generic API runs parallel to legacy; feature flag switches traffic
2. **Zero user-visible change** — same URLs, same screens, same business outcomes
3. **Data preservation** — no destructive migration of existing `journal_entries`, `revenue_invoices`, `procurement_invoices`
4. **Regression parity** — automated comparison of findings/risk output before/after per fixture file
5. **Additive DB only** — new generic tables added; legacy tables deprecated gradually (ADR-006)

---

## 2.2 Journal Entry Testing

### Current Architecture

| Layer | Implementation |
|-------|----------------|
| Routers | `upload.py`, `rules.py`, `analytics.py` (root paths) |
| Services | `upload_service`, `excel_validator`, `rule_runner`, `rule_engine`, `risk_scoring`, `findings_service` |
| Tables | `journal_entries`, `rule_results`, `risk_scores` |
| Frontend | `JournalEntryTestingWorkspace` + 13 components |
| APIs | `/upload`, `/run-rules`, `/run-risk`, `/generate-findings`, etc. |

### Target Architecture

| Layer | Implementation |
|-------|----------------|
| Plugin | `JournalEntryPlugin` implementing `ModuleProvider` |
| APIs | `/api/v2/modules/JOURNAL_ENTRY_TESTING/*` (+ legacy shim) |
| Tables | Keep `journal_entries`, `rule_results`, `risk_scores` initially; adapter implements `RecordRepository` |
| Frontend | `AuditModuleWorkspace moduleCode="JOURNAL_ENTRY_TESTING"`; journal-specific `FindingsTable` as UI slot |
| Config | `module_plugin_config` seeded from `constants.py` + `FINDING_TEMPLATES` |

### Migration Approach

| Phase | Action |
|-------|--------|
| M2.1 | Extract `JournalEntryPlugin`; register in registry |
| M2.2 | Implement generic engines calling plugin; unit tests with journal fixtures |
| M2.3 | Add `/api/v2/modules/JOURNAL_ENTRY_TESTING/*` routes |
| M2.4 | Legacy routes delegate to generic engines (thin shim) |
| M2.5 | Switch `JournalEntryTestingWorkspace` to generic workspace behind `USE_GENERIC_WORKSPACE` flag |
| M2.6 | Regression test: upload `sample_journal_entries.xlsx` → compare findings |
| M2.7 | Remove shim code after 2-week bake period |

### Risks

| Risk | Mitigation |
|------|------------|
| Debit/credit validation differs | Golden-file regression tests |
| `rule_config.py` merge logic lost | Port into plugin config merge |
| Journal uses root API paths in frontend | API client abstraction layer |

### Backward Compatibility

- Legacy `/upload`, `/run-rules` remain as aliases for minimum 1 release
- `Deprecation: true` + `Sunset` headers per ADR-005
- `project_type = journal_testing` unchanged

### Testing Strategy

- 7 rule codes × fixture files → expected violation counts
- Integration: full pipeline HTTP test
- E2E: Playwright journal workflow
- Performance: 10k row journal file via worker queue

---

## 2.3 Revenue Testing

### Current Architecture

| Layer | Implementation |
|-------|----------------|
| Router | `revenue.py` (`/revenue/*`) |
| Services | `revenue_*` (7 files) |
| Tables | `revenue_invoices`, `revenue_rule_results`, `revenue_risk_scores` |
| Frontend | `RevenueTestingWorkspace` + 11 components |
| APIs | `/revenue/upload`, `/revenue/run-rules`, etc. |

### Target Architecture

- `RevenuePlugin` + generic engines
- `/api/v2/modules/REVENUE_TESTING/*`
- UI slot: `InvoiceFindingsTable` (replaces `RevenueFindingsTable`)
- Theme: indigo (from `ui_config`)

### Migration Approach

Same strangler pattern as journal. Revenue is second because it validates invoice-style plugins (shared pattern with procurement and 15+ future modules).

### Risks

| Risk | Mitigation |
|------|------------|
| GST validation edge cases | India-specific test fixtures |
| `journal_entry_ids` JSONB column misnamed for invoice IDs | Document; alias in API response as `affected_entity_ids` |

### Backward Compatibility

- `/revenue/*` shims to generic routes
- Report types `revenue_audit_*` unchanged

### Testing Strategy

- 7 `REV_*` rules with sales register fixtures
- Cross-tenant isolation test
- E2E revenue workflow

---

## 2.4 Procurement Testing

### Current Architecture

| Layer | Implementation |
|-------|----------------|
| Router | `procurement.py` (`/procurement/*`) |
| Services | `procurement_*` (7 files) |
| Tables | `procurement_invoices`, `procurement_rule_results`, `procurement_risk_scores` |
| Frontend | `ProcurementTestingWorkspace` + 11 components |

### Target Architecture

- `ProcurementPlugin` + generic engines
- `/api/v2/modules/PROCUREMENT_TESTING/*`
- UI slot: `VendorInvoiceFindingsTable`
- Theme: teal

### Migration Approach

Third in sequence (highest similarity to revenue — validates generic invoice plugin pattern).

### Risks

| Risk | Mitigation |
|------|------------|
| PO matching logic in `PROC_MISSING_PO` | Preserve evaluator verbatim in plugin |
| Near-duplicate of revenue | Abstract shared `InvoiceModuleBase` mixin in plugin layer only |

### Backward Compatibility

- `/procurement/*` shims
- Report types unchanged

### Testing Strategy

- 7 `PROC_*` rules with vendor invoice fixtures
- Parity test vs legacy procurement endpoints

---

## 2.5 Migration Feature Flags

| Flag | Scope | Default |
|------|-------|---------|
| `USE_GENERIC_MODULES_API` | Backend routing | `false` → `true` per module |
| `USE_GENERIC_WORKSPACE` | Frontend workspace | `false` → `true` per module |
| `USE_ANALYSIS_RUN_PIPELINE` | Run orchestration | `false` → `true` |

---

# Part 3 — Remaining Audit Modules (19)

## 3.1 Implementation Tiers

After migration, new modules are delivered in three tiers:

| Tier | Effort | When to Use | Code Required |
|------|--------|-------------|---------------|
| **Tier 1 — Config-only** | 1–3 days | Simple rule-based modules on existing entity types | JSON config + `rules_master` seeds only |
| **Tier 2 — Plugin-light** | 1–2 weeks | New columns/validators but shared invoice/ledger engine | `ModuleProvider` + evaluators |
| **Tier 3 — Plugin-full** | 2–4 weeks | Novel data models (bank lines, access logs, payroll) | Full plugin + new record adapter + UI slot |

---

## 3.2 Module Implementation Matrix

| # | Module | Tier | Input Entity | Key Rules (examples) | Reports | UI Slot |
|---|--------|------|--------------|----------------------|---------|---------|
| 4 | Ledger Scrutiny | 2 | GL account balances | Variance, trend, anomaly | Excel scrutiny report | Account variance table |
| 5 | Duplicate Payment Checking | 1 | Vendor payments (reuse procurement) | Duplicate payment, overlap | Exception list | Reuse invoice table |
| 6 | Bank Reconciliation | 3 | Bank statement lines | Unmatched, timing diff | Recon working paper | Bank match grid |
| 7 | GST Mismatch Checking | 2 | GST returns + books | GSTR-1 vs books, rate errors | GST variance report | GST summary |
| 8 | PO Matching | 2 | PO + GRN + Invoice | Three-way match failures | PO exception report | Match status table |
| 9 | Vendor Invoice Validation | 2 | Vendor invoices (reuse) | Validity, approval limits | Invoice exception report | Reuse invoice table |
| 10 | Expense Claim Verification | 2 | Expense claims | Policy breach, duplicate | Expense exception report | Claim line table |
| 11 | Fixed Asset Verification | 2 | Asset register | Missing asset, cap policy | Asset verification report | Asset list table |
| 12 | Depreciation Recalculation | 2 | Asset register + schedules | Variance from recorded | Depreciation report | Asset schedule table |
| 13 | TDS Deduction Checking | 2 | Payment register | Rate, section, challan | TDS exception report | TDS line table |
| 14 | GST ITC Validation | 2 | Purchase + GSTR-2B | ITC ineligible, mismatch | ITC report | ITC summary |
| 15 | Customer Balance Confirmation | 2 | AR balances | Unconfirmed, variance | Confirmation tracker | Customer list |
| 16 | Payroll Audit Checking | 3 | Payroll register | Statutory, headcount | Payroll exception report | Payroll line table |
| 17 | User Access Review | 3 | Access log export | Excessive privilege, dormant | Access review report | User access table |
| 18 | Segregation of Duties | 3 | Role matrix | Conflicting roles | SoD report | Conflict matrix |
| 19 | Compliance Checklist | 1 | Checklist JSON | Incomplete items | Compliance status | Checklist UI |
| 20 | Supporting Document Matching | 2 | Transactions + docs | Missing support | Document match report | Match table |
| 21 | Exception Report Preparation | 1 | Aggregated findings | Unresolved exceptions | Exception report | Reuse findings panel |
| 22 | Invoice Checking | 2 | Sales/purchase invoices | Arithmetic, tax, completeness | Invoice check report | Invoice table |

---

## 3.3 Required Configuration per Module

Every new module requires a `module_plugin_config` row:

```yaml
required:
  input_schema:        # columns, types, required fields
  validation_rules:    # row + aggregate rules
  rule_codes:          # entries in rules_master
  finding_templates:   # per rule_code
  report_types:        # at least one export format
  kpi_cards:           # summary metrics for workspace
  ui_config:           # accent, stepper, labels
optional:
  custom_evaluators:   # Python functions for Tier 2/3
  ui_slot_component:   # React component name for line-level table
  ai_prompts:          # Phase 3 M4
  materiality_overrides: # Phase 3 M8
```

---

## 3.4 Minimal-Code Module Addition Process

```
1. Add row to audit_module_catalog (implementation_status = beta)
2. Seed rules_master with rule_codes + default_score
3. Insert module_plugin_config JSON
4. If Tier 2/3: implement ModuleProvider subclass (evaluators only)
5. If custom UI: add one UiSlot component
6. Enable for pilot org via feature flag
7. Run acceptance test suite template
8. Set implementation_status = built
```

**No new router file. No new workspace file. No new upload service.**

Estimated: **Tier 1 = 1–3 days**, **Tier 2 = 1–2 weeks**, **Tier 3 = 2–4 weeks** per module.

---

## 3.5 Build Priority (Phase 3 M3)

| Wave | Modules | Rationale |
|------|---------|-----------|
| P1 | GST Mismatch, Bank Reconciliation, Payroll | High demand India market |
| P2 | Ledger Scrutiny, Duplicate Payment, Invoice Checking | Extends existing patterns |
| P3 | Fixed Asset, TDS, PO Matching, Vendor Invoice | Standard audit procedures |
| P4 | IT Controls (User Access, SoD), Compliance, remaining | Enterprise tier |

---

# Part 4 — Architecture Principles

## 4.1 Generic Platform (shared by every module)

| Component | Scope |
|-----------|-------|
| Module Registry & catalog | All |
| Generic Upload / Validation / Rule / Risk / Findings / Report / Analysis engines | All |
| Generic REST API (`/api/v2/modules/{code}/*`) | All |
| `AuditModuleWorkspace` shell | All |
| `audit_findings` lifecycle + review workflow | All |
| `rules_master` config store | All |
| Engagement team, evidence, workpapers | All |
| Analysis runs + Official Run | All |
| Tenant isolation (`TenantContext`) | All |
| Subscription plan gating | All |
| Audit logs | All |
| Blob storage adapter | All |
| Job queue + workers | All |
| Usage metering | All |
| Executive dashboard shell | All |
| Notifications infrastructure | All |

## 4.2 Module Plugins (unique per module)

| Component | Scope |
|-----------|-------|
| `input_schema` (columns, types) | Per module |
| `validation_rules` | Per module |
| `rule_evaluators` (business logic) | Per module |
| `finding_templates` | Per module |
| `report_templates` / KPI definitions | Per module |
| `ui_config` (theme, labels, stepper) | Per module |
| Optional `UiSlot` components | Per module |
| AI prompts (Phase 3 M4) | Per module |
| Materiality overrides (Phase 3 M8) | Per module |

---

## 4.3 Change Impact Matrix

| Change | Impact Scope | Modules Affected | Effort |
|--------|--------------|------------------|--------|
| Improve Upload Engine | **Platform** | All 22+ | Low (one PR) |
| Improve Validation Engine | **Platform** | All 22+ | Low |
| Improve Rule Engine orchestration | **Platform** | All 22+ | Low |
| Improve Risk Engine thresholds UI | **Platform** | All 22+ | Low |
| Improve Findings Engine grouping | **Platform** | All 22+ | Low |
| Improve Report Engine PDF layout | **Platform** | All 22+ | Low |
| Improve Analysis Run worker | **Platform** | All 22+ | Medium |
| Add Journal-specific rule `MANUAL_JOURNAL` | **Plugin** | Journal only | Low |
| Change GST validation logic | **Plugin** | GST, Revenue, Procurement, ITC | Medium |
| Change bank matching algorithm | **Plugin** | Bank Reconciliation only | Low |
| New payroll statutory rule | **Plugin** | Payroll only | Low |
| New UI table for SoD matrix | **Plugin UI** | SoD only | Medium |
| Subscription plan module list | **Platform config** | Per plan | Low |
| Tenant isolation fix | **Platform** | All | Critical |

---

# Part 5 — Database Design

## 5.1 Existing Tables (retained)

### Platform / SaaS

| Table | Purpose |
|-------|---------|
| `organizations` | Tenant root |
| `organization_members` | RBAC membership |
| `subscription_plans` | Plan definitions |
| `organization_subscriptions` | Active plan per org |
| `users`, `refresh_tokens` | Auth |
| `audit_logs` | Mutation audit trail |

### Audit hierarchy

| Table | Purpose |
|-------|---------|
| `clients` | Client master |
| `audit_engagements` | Engagement per client/FY |
| `audit_projects` | Module workspace (`project_type`) |

### Module catalog (existing)

| Table | Purpose |
|-------|---------|
| `audit_module_catalog` | 22 module registry |
| `engagement_enabled_modules` | Per-engagement enablement |
| `module_analysis_runs` | Analysis run lifecycle |

### Phase 2 workflow (existing)

| Table | Purpose |
|-------|---------|
| `engagement_team_members` | Team assignments |
| `engagement_team_assignment_history` | Team audit trail |
| `evidence`, `workpapers`, `evidence_links` | Evidence repository |
| `audit_findings`, `finding_status_history` | Finding lifecycle |
| `review_comments`, `approvals` | Review workflow |
| `report_history` | Consolidated reports |

### Per-module data (existing — retained during migration)

| Module | Tables |
|--------|--------|
| Journal | `journal_entries`, `rule_results`, `risk_scores` |
| Revenue | `revenue_invoices`, `revenue_rule_results`, `revenue_risk_scores` |
| Procurement | `procurement_invoices`, `procurement_rule_results`, `procurement_risk_scores` |
| Shared | `rules_master`, `reports` |

---

## 5.2 New Tables (Phase 3)

| Table | Purpose | Milestone |
|-------|---------|-----------|
| `module_plugin_config` | JSON config per module (schema, templates, UI) | M1 |
| `module_rule_results` | Generic rule results (optional — phased) | M1/M2 |
| `module_risk_scores` | Generic risk scores (optional — phased) | M1/M2 |
| `module_records` | Generic uploaded record store (optional — long-term) | M10 |
| `usage_records` | Upload/storage/AI credit metering | M5 |
| `ai_recommendations` | LLM outputs + confidence + approval state | M4 |
| `ai_prompt_versions` | Prompt audit trail | M4 |
| `notifications` | In-app notifications | M8 |
| `materiality_settings` | Per-engagement materiality | M8 |
| `audit_samples` | Sampling methodology records | M8 |
| `report_templates` | Firm-branded report layouts | M6 |
| `feature_flags` | Org/module feature toggles | M1 |
| `api_keys` | Enterprise API access (Big Four) | M7 |

---

## 5.3 Modified Tables (additive columns only)

| Table | New Columns |
|-------|-------------|
| `audit_module_catalog` | `project_type`, `rule_prefix`, `input_format`, `theme_color`, `ui_config` (JSONB) |
| `module_analysis_runs` | `is_official`, `locked_at`, `locked_by`, `pipeline_step`, `error_detail` |
| `audit_findings` | `module_code`, `analysis_run_id`, `affected_entity_ids` (rename from `journal_entry_ids` via view) |
| `organization_subscriptions` | `stripe_subscription_id`, `billing_cycle_anchor` |
| `users` | `mfa_secret`, `mfa_enabled`, `sso_provider`, `sso_subject` |

---

## 5.4 ER Diagram (description)

```
organizations ──┬── organization_members ── users
                ├── organization_subscriptions ── subscription_plans
                ├── clients ── audit_engagements ──┬── audit_projects
                │                                 ├── engagement_enabled_modules ── audit_module_catalog
                │                                 ├── engagement_team_members
                │                                 ├── evidence / workpapers
                │                                 ├── module_analysis_runs
                │                                 ├── materiality_settings
                │                                 └── audit_samples
                │
audit_module_catalog ── module_plugin_config
                     └── rules_master (shared rule defs)

audit_projects ──┬── [module-specific records]  (journal_entries | revenue_invoices | ...)
                 ├── module_rule_results (generic — phased)
                 ├── module_risk_scores (generic — phased)
                 ├── audit_findings ── finding_status_history
                 │                  └── review_comments / approvals
                 └── reports ── report_history

usage_records ── organizations
ai_recommendations ── audit_findings / module_analysis_runs
notifications ── users
```

---

## 5.5 Migration Strategy for Data Model

| Phase | Approach |
|-------|----------|
| M1 | Add `module_plugin_config`; extend catalog columns |
| M2 | Plugins use existing per-module tables via adapters |
| M3+ | New modules use generic `module_rule_results` where possible |
| M10 | Evaluate consolidation of per-module record tables into `module_records` (JSONB + indexed keys) — only if performance testing warrants |

**Decision:** Do **not** big-bang migrate `journal_entries` / `revenue_invoices` to generic storage in M1–M3. Use **adapter pattern** to avoid data migration risk.

---

# Part 6 — API Design

## 6.1 Existing APIs (preserved during transition)

| Group | Prefix | Status |
|-------|--------|--------|
| Auth | `/auth/*` | Keep |
| Organizations | `/organizations/*` | Keep |
| Subscriptions | `/subscriptions/*` | Keep |
| Clients / Engagements / Projects | `/clients`, `/engagements`, `/projects` | Keep |
| Journal (legacy) | `/upload`, `/run-rules`, `/run-risk`, `/generate-findings`, `/findings`, `/reports` | Shim → generic |
| Revenue (legacy) | `/revenue/*` | Shim → generic |
| Procurement (legacy) | `/procurement/*` | Shim → generic |
| Phase 2 | `/engagements/{id}/team|evidence|workpapers|findings|runs|hub` | Keep |
| Catalog | `/modules/catalog` | Keep |

## 6.2 Generic APIs (new — Phase 3 M1)

**Version prefix:** `/api/v2/`

```
GET    /api/v2/modules/catalog
GET    /api/v2/modules/{code}/metadata
POST   /api/v2/modules/{code}/upload
POST   /api/v2/modules/{code}/run-rules
POST   /api/v2/modules/{code}/run-risk
GET    /api/v2/modules/{code}/risk-scores
POST   /api/v2/modules/{code}/generate-findings
GET    /api/v2/modules/{code}/findings
POST   /api/v2/modules/{code}/reports/generate
GET    /api/v2/modules/{code}/reports
```

## 6.3 Phase 3 Platform APIs (by milestone)

| Milestone | API Group |
|-----------|-----------|
| M4 AI | `/api/v2/ai/narratives`, `/api/v2/ai/recommendations/{id}/approve` |
| M5 Billing | `/api/v2/billing/usage`, `/webhooks/stripe` |
| M6 Executive | `/api/v2/firm/dashboard`, `/api/v2/firm/engagements/summary` |
| M7 Security | `/api/v2/auth/mfa/*`, `/api/v2/auth/sso/*` |
| M8 Notifications | `/api/v2/notifications` |
| M8 Materiality | `/api/v2/engagements/{id}/materiality`, `/api/v2/engagements/{id}/samples` |

## 6.4 API Versioning Strategy

| Version | Scope | Policy |
|---------|-------|--------|
| v1 (implicit) | Legacy root paths | Deprecated after M2; sunset headers |
| v2 | Generic module platform | Stable; additive changes only |
| v3 (future) | GraphQL / federation | Post Phase 3 |

- `Accept-Version: v2` header
- OpenAPI spec published at `/api/v2/openapi.json`
- Contract tests in CI per ADR-005

## 6.5 Routing Strategy

```python
# FastAPI mount structure
app.include_router(auth_router)
app.include_router(platform_router)          # orgs, clients, engagements
app.include_router(phase2_router)            # team, evidence, runs, hub
app.include_router(module_catalog_router)
app.include_router(create_generic_module_router())  # dynamic per registered plugin
app.include_router(legacy_shim_router)       # /upload, /revenue/*, /procurement/*
```

---

# Part 7 — Frontend Design

## 7.1 Design Principle

> **Same screens, same navigation, same module cards — generic engine under the hood.**

Users continue to see:

- 22 Audit Modules grid
- 3 Active / 19 Coming Soon
- Journal Entry / Revenue / Procurement workspaces with current branding
- Engagements → Findings / Evidence / Team / Modules panels

## 7.2 Generic Workspace Structure

```
components/module-workspace/
├── AuditModuleWorkspace.tsx       # Orchestrator (replaces 3 workspace files)
├── ModulePageHeader.tsx           # Config-driven header
├── ClientEngagementSection.tsx      # Moved from journal-entry-testing (shared)
├── ProjectSelectionSection.tsx    # Generic, filtered by project_type
├── FileUploadSection.tsx          # Generic, column hints from metadata
├── ValidationPanel.tsx            # Generic, validation result display
├── AnalysisSection.tsx            # Generic, rule list from metadata
├── ResultsSummaryCards.tsx        # Generic, KPI cards from config
├── AuditFindingsPanel.tsx         # Existing shared component
├── FindingsTable.tsx              # Generic fallback table
├── ExportSection.tsx              # Generic, report types from config
├── WorkflowStepper.tsx            # Optional, config-driven steps
└── slots/
    ├── JournalLineFindingsTable.tsx
    ├── InvoiceFindingsTable.tsx     # Shared by revenue + procurement + invoice modules
    └── ...
```

## 7.3 Shared Components (promoted)

From current `journal-entry-testing/`:

- `SectionCard`
- `ClientEngagementSection`
- `AuditFindingsPanel`

From `dashboard/`:

- `AuditModulesGrid`, `AuditModuleCard` (unchanged)
- `EngagementFindingsPanel`, `EngagementTeamPanel`, `EngagementRepositoryPanel`, `EngagementModulesPanel` (unchanged)

## 7.4 Module-Specific Components

Only when generic table cannot render entity-specific columns:

| Module | Slot Component |
|--------|----------------|
| Journal Entry | `JournalLineFindingsTable` (debit/credit columns) |
| Revenue / Procurement / Invoice Checking | `InvoiceFindingsTable` |
| Bank Reconciliation | `BankReconMatchGrid` |
| Segregation of Duties | `SoDConflictMatrix` |
| Compliance Checklist | `ComplianceChecklistPanel` |

## 7.5 Dynamic Navigation

- Sidebar unchanged (`lib/dashboard/navigation.ts`)
- `AuditModuleCard` → `hrefForModuleSlug()` → dedicated route or `[slug]`
- Built modules: render `AuditModuleWorkspace`
- Planned modules: `ModuleDetailClient` Coming Soon (unchanged)

## 7.6 Module Loading Strategy

```tsx
// app/dashboard/ai-modules/revenue-testing/page.tsx (unchanged route)
export default function RevenueTestingPage() {
  return (
    <DashboardShell title="Revenue Testing" subtitle="...">
      <AuditModuleWorkspace moduleCode="REVENUE_TESTING" />
    </DashboardShell>
  );
}
```

- Metadata fetched on mount: `GET /api/v2/modules/REVENUE_TESTING/metadata`
- API calls use generic client: `moduleApi.upload(code, projectId, file)`
- Feature flag `USE_GENERIC_WORKSPACE` in `.env.local` for gradual rollout

---

# Part 8 — Performance & Scalability

## 8.1 Target Scale

| Dimension | Phase 3 Target | Long-term |
|-----------|----------------|-----------|
| Modules | 22 | 100+ |
| Organizations | 1,000 | 10,000+ |
| Users per org | 50 | 500+ |
| Rows per upload | 100,000 | 1,000,000+ |
| Concurrent analysis runs | 50 platform-wide | 500+ |
| Storage per org | 10 GB | 1 TB (enterprise) |

## 8.2 Framework Scalability Assessment

| Concern | Supported? | Notes |
|---------|------------|-------|
| 22 modules | ✅ Yes | Registry + config-driven |
| 50 modules | ✅ Yes | Tier 1 config-only modules |
| 100+ modules | ⚠️ With caveats | Need module grouping UI, lazy loading, search |
| Thousands of orgs | ✅ Yes | Existing `organization_id` tenant model |
| Large datasets | ⚠️ Requires workers | Sync HTTP insufficient; Redis queue mandatory |
| Parallel analysis | ⚠️ M1 infra | Worker pool per org fair-queue |
| No architectural redesign for new modules | ✅ Yes | Plugin + config pattern |

## 8.3 Performance Design Decisions

| Decision | Rationale |
|----------|-----------|
| Async analysis via Redis workers | Prevent HTTP timeout on 100k rows |
| Pagination on all list endpoints | Already Phase 2 pattern; enforce everywhere |
| Indexed `organization_id` on all tenant tables | Query performance |
| Blob storage off API server | Memory + disk pressure |
| Read replicas for executive dashboard | M10 |
| Redis cache for catalog + engagement hub | Reduce repeated aggregation |
| Partition `audit_logs` / `audit_findings` by month | M10 |

## 8.4 Identified Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Sync rule execution in HTTP | High | Worker queue in M1 |
| Per-module table sprawl | Medium | Generic results tables for new modules |
| Noisy neighbor (one firm large upload) | High | Per-org fair queue + plan limits |
| Catalog grid with 100 modules | Low | Search + category filter UI |
| JSONB `module_records` query perf | Medium | Benchmark before migrating legacy tables |

---

# Part 9 — Testing Strategy

## 9.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  Playwright: 5 critical paths
                   ┌┴─────────┴┐
                   │ Integration│  pytest + TestClient: API contracts
                  ┌┴───────────┴┐
                  │    Unit     │  pytest: engines, plugins, RBAC
                  └─────────────┘
```

## 9.2 Test Types

| Type | Scope | Tools |
|------|-------|-------|
| Unit | Engines, plugins, validators, evaluators | pytest |
| Integration | Generic API, tenant isolation, migration parity | pytest + httpx |
| Regression | Legacy vs generic output comparison | Golden fixture files |
| Migration | Data integrity, shim correctness | Custom parity scripts |
| E2E | Login → hub → upload → analyze → findings | Playwright |
| Performance | 100k row upload, 100 concurrent firms | k6 / Locust |
| Security | IDOR, cross-tenant, rate limits | pytest + OWASP ZAP |
| Contract | OpenAPI v2 schema | schemathesis |

## 9.3 Acceptance Criteria per Milestone

### M1 — Generic Module Framework

- [ ] `ModuleProvider` protocol defined and documented
- [ ] Registry loads 3 plugins at startup
- [ ] Generic upload/validate/rules/risk/findings work with mock plugin
- [ ] `module_plugin_config` seeded for 3 modules
- [ ] Unit test coverage ≥ 80% on engines
- [ ] OpenAPI v2 spec published

### M2 — Existing Module Migration

- [ ] Journal findings parity: 100% match on fixture files vs legacy
- [ ] Revenue findings parity: 100% match
- [ ] Procurement findings parity: 100% match
- [ ] Legacy shims return identical responses
- [ ] `AuditModuleWorkspace` renders all 3 modules identically to current UI (visual regression)
- [ ] E2E passes for all 3 workflows
- [ ] Zero user-facing URL changes

### M3 — Remaining Audit Modules

- [ ] P1 modules (GST, Bank Recon, Payroll) added via plugin only — no new routers
- [ ] Each module has ≥ 5 rule codes and ≥ 1 report type
- [ ] Catalog shows correct Active/Coming Soon counts
- [ ] Subscription gating enforced per module

### M4 — AI Engine

- [ ] AIService with provider abstraction (OpenAI + Azure)
- [ ] PII redaction before LLM call
- [ ] AI output requires auditor approval before export
- [ ] `ai_recommendations` table populated
- [ ] AI credits deducted from `usage_records`

### M5 — AI Usage & Billing

- [ ] `usage_records` tracks uploads, storage, AI credits
- [ ] Plan limits enforced at API layer
- [ ] Stripe webhook activates subscription
- [ ] Usage dashboard in Settings

### M6 — Executive Dashboard

- [ ] Firm-wide KPIs: engagements, findings, risk, team utilization
- [ ] Cross-engagement drill-down
- [ ] P95 dashboard load < 2s with 100 engagements

### M7 — Enterprise Security

- [ ] MFA (TOTP) enrollment and login
- [ ] SSO via Azure AD (OIDC)
- [ ] API rate limiting per plan
- [ ] Server-side auth middleware on `/dashboard/*`
- [ ] Security audit log complete

### M8 — Notifications & Materiality

- [ ] In-app notifications for review assignments, run completion
- [ ] Materiality settings per engagement
- [ ] Sampling records linked to findings

### M9 — Quality & DevOps

- [ ] CI/CD: lint, pytest, build, Playwright on every PR
- [ ] Staging environment deploys automatically
- [ ] Feature flag framework operational

### M10 — Scalability

- [ ] 100-firm load test passed
- [ ] 100k row analysis completes via worker < 5 min
- [ ] Read replica routing for dashboard
- [ ] Partition strategy documented for `audit_logs`

---

# Part 10 — Risk Assessment

## 10.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Migration parity failure | Medium | High | Golden-file regression; strangler pattern |
| Plugin interface wrong abstraction | Medium | High | Migrate 3 diverse modules first; iterate before M3 |
| Generic DB model performance | Low | Medium | Adapter pattern; benchmark before consolidate |
| Analysis run worker failure | Medium | High | Retry + dead letter queue; status visible in UI |

## 10.2 Migration Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking legacy API consumers | Medium | High | Shims + deprecation headers; 2-release sunset |
| Frontend visual regression | Medium | Medium | Playwright visual snapshots |
| Data loss during migration | Low | Critical | Additive-only migrations; no destructive DDL |

## 10.3 Performance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| HTTP timeout on large files | High | High | Worker queue mandatory before marketing scale |
| DB connection exhaustion | Medium | High | Connection pooling; PgBouncer |
| Redis single point of failure | Medium | Medium | Redis Sentinel or managed Redis |

## 10.4 Security Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM hallucination in audit context | High | Critical | Rules remain source of truth; human approval |
| PII sent to LLM | Medium | Critical | Redaction pipeline; data minimization |
| Cross-tenant data leak | Low | Critical | Integration tests Firm A vs B; remove legacy `user_id` fallback |
| Plugin code execution vulnerability | Low | High | Sandboxed evaluators; no arbitrary code in config-only modules |

## 10.5 Maintenance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Config JSON drift from code | Medium | Medium | JSON schema validation; CI check |
| 22 modules overwhelm support | Medium | Medium | Tiered rollout; beta flags |
| Documentation lag | High | Medium | Update docs per milestone (mandatory gate) |

---

# Part 11 — Execution Plan

## 11.1 Implementation Order

```
M1 Generic Framework
 ↓
M2 Migrate 3 Modules
 ↓
M3 Remaining Modules (P1 → P4 waves)
 ↓
M4 AI Engine
 ↓
M5 AI Usage & Billing
 ↓
M6 Executive Dashboard
 ↓
M7 Enterprise Security
 ↓
M8 Notifications & Materiality
 ↓
M9 Quality & DevOps
 ↓
M10 Scalability
```

**Estimated total duration:** 24–36 weeks (single team); 16–24 weeks with parallel tracks.

---

## 11.2 Milestone Details

### Milestone 1 — Generic Module Framework

| Item | Detail |
|------|--------|
| **Objectives** | Build plugin host, registry, generic engines, v2 API skeleton |
| **Deliverables** | `ModuleProvider` protocol, `ModuleRegistry`, 6 engines, `module_plugin_config` table, `/api/v2/modules/{code}/*` router factory, unit tests |
| **Database** | `module_plugin_config`; extend `audit_module_catalog`; `feature_flags` |
| **API** | v2 generic module endpoints (mock plugin) |
| **Frontend** | `AuditModuleWorkspace` shell (no module migration yet) |
| **Testing** | Engine unit tests; registry load tests |
| **Risks** | Wrong abstraction — mitigated by designing against 3 real modules |
| **Branch** | `phase3/m1-generic-framework` → `architecture` |

---

### Milestone 2 — Existing Module Migration

| Item | Detail |
|------|--------|
| **Objectives** | Migrate Journal, Revenue, Procurement to GMMF with zero user impact |
| **Deliverables** | 3 plugins, legacy shims, generic workspace live, regression parity report |
| **Database** | Seed `module_plugin_config` for 3 modules; optional `module_rule_results` |
| **API** | Legacy paths shim to v2; deprecation headers |
| **Frontend** | 3 dedicated routes render `AuditModuleWorkspace`; visual parity |
| **Testing** | Golden-file regression; E2E 3 workflows; visual regression |
| **Risks** | Parity failure — block release until 100% match |
| **Branch** | `phase3/m2-module-migration` → `architecture` |

---

### Milestone 3 — Remaining Audit Modules

| Item | Detail |
|------|--------|
| **Objectives** | Deliver P1–P4 catalog modules via plugin/config |
| **Deliverables** | GST Mismatch, Bank Reconciliation, Payroll (P1); 6+ more modules |
| **Database** | `rules_master` seeds per module; config rows |
| **API** | No new routers — only registry entries |
| **Frontend** | New UiSlots where needed; catalog status → Active |
| **Testing** | Per-module acceptance template (5 rules, 1 report, 1 E2E) |
| **Risks** | Reverting to copy-paste — enforce "no new router" PR check |
| **Branch** | `phase3/m3-modules-p1`, `phase3/m3-modules-p2`, etc. |

---

### Milestone 4 — AI Engine

| Item | Detail |
|------|--------|
| **Objectives** | LLM-assisted narratives with human approval |
| **Deliverables** | `AIService`, `ai_recommendations`, `ai_prompt_versions`, PII redaction, approval UI |
| **Database** | `ai_recommendations`, `ai_prompt_versions` |
| **API** | `/api/v2/ai/*` |
| **Frontend** | AI narrative panel on findings; approve/reject before export |
| **Testing** | Mock LLM in CI; redaction unit tests; approval workflow E2E |
| **Risks** | Hallucination — rules remain authoritative; AI is advisory only |
| **Branch** | `phase3/m4-ai-engine` |

---

### Milestone 5 — AI Usage & Billing

| Item | Detail |
|------|--------|
| **Objectives** | Meter usage; enforce plan limits; Stripe billing |
| **Deliverables** | `usage_records`, usage API, Stripe webhooks, usage UI in Settings |
| **Database** | `usage_records`; extend `organization_subscriptions` |
| **API** | `/api/v2/billing/*`, `/webhooks/stripe` |
| **Frontend** | Usage meters in Settings; plan upgrade flow |
| **Testing** | Credit deduction tests; webhook signature verification |
| **Risks** | Incorrect metering — dual-write validation period |
| **Branch** | `phase3/m5-billing` |

---

### Milestone 6 — Executive Dashboard

| Item | Detail |
|------|--------|
| **Objectives** | Firm-wide KPIs for partners |
| **Deliverables** | Executive dashboard page, firm summary API, report templates |
| **Database** | `report_templates`; optional materialized views |
| **API** | `/api/v2/firm/dashboard` |
| **Frontend** | `/dashboard/executive` (new nav item for partner role) |
| **Testing** | Performance test 100 engagements; RBAC (partner only) |
| **Risks** | Slow aggregations — Redis cache + read replica |
| **Branch** | `phase3/m6-executive-dashboard` |

---

### Milestone 7 — Enterprise Security

| Item | Detail |
|------|--------|
| **Objectives** | MFA, SSO, rate limiting, server-side auth |
| **Deliverables** | TOTP MFA, Azure AD OIDC, API rate limiter, Next.js middleware |
| **Database** | `users.mfa_*`, `users.sso_*` |
| **API** | `/api/v2/auth/mfa/*`, `/api/v2/auth/sso/*` |
| **Frontend** | MFA enrollment; SSO login button |
| **Testing** | MFA bypass attempts; rate limit exceeded; middleware redirect |
| **Risks** | SSO IdP misconfiguration — staging IdP first |
| **Branch** | `phase3/m7-enterprise-security` |

---

### Milestone 8 — Notifications & Materiality

| Item | Detail |
|------|--------|
| **Objectives** | User alerts; engagement materiality; sampling |
| **Deliverables** | Notification center, materiality settings, sample records |
| **Database** | `notifications`, `materiality_settings`, `audit_samples` |
| **API** | `/api/v2/notifications`, materiality endpoints |
| **Frontend** | Notification bell; materiality panel on engagement |
| **Testing** | Notification delivery; materiality threshold affects risk engine |
| **Risks** | Notification noise — user preferences |
| **Branch** | `phase3/m8-notifications-materiality` |

---

### Milestone 9 — Quality & DevOps

| Item | Detail |
|------|--------|
| **Objectives** | CI/CD, staging, feature flags, documentation sync |
| **Deliverables** | GitHub Actions pipeline, Playwright E2E, staging env, feature flag service |
| **Database** | `feature_flags` |
| **API** | Admin feature flag API |
| **Frontend** | None (infra) |
| **Testing** | CI green on every PR; E2E on staging deploy |
| **Risks** | CI flakiness — retry policy; test isolation |
| **Branch** | `phase3/m9-devops` |

---

### Milestone 10 — Scalability

| Item | Detail |
|------|--------|
| **Objectives** | Validate 100-firm scale; optimize bottlenecks |
| **Deliverables** | Load test report, read replica routing, partition plan, caching layer |
| **Database** | Partition strategy; indexes review |
| **API** | Read replica routing middleware |
| **Frontend** | Catalog search for 50+ modules |
| **Testing** | k6 100-firm / 500-user load test |
| **Risks** | Load test fails — identify bottleneck per report |
| **Branch** | `phase3/m10-scalability` |

---

## 11.3 Git Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production releases |
| `architecture` | Integration branch (current) |
| `phase3/m{N}-{name}` | Short-lived milestone branches |
| `phase3/m3-modules-{module}` | Individual module plugins |

**Rules:**

- No force push to `main`
- PR required with CI green
- Milestone branches merge to `architecture`; `architecture` → `main` at release gates
- Feature flags control production exposure

---

## 11.4 Parallel Work Streams (optional)

| Stream A | Stream B |
|----------|----------|
| M1 → M2 → M3 | M9 (CI/CD) early |
| M4 → M5 | M7 (Security) after M2 |
| M6 → M8 | M10 after M3 |

---

# Final Review

## Architectural Weaknesses Identified

| Weakness | Severity | Correction Before Implementation |
|----------|----------|-------------------------------|
| `audit_findings.journal_entry_ids` misnamed for all entity types | Medium | Add `affected_entity_ids` API alias; migrate column in M2 |
| Analysis run worker is stub | High | Wire `AnalysisEngine` in M1, not M2 |
| Dashboard service is journal-only | Medium | Extend in M6 for executive dashboard |
| Dual tenant model (`user_id` + `organization_id`) | High | Complete Wave 0 removal of legacy fallback before M3 |
| No API versioning today | Medium | Introduce `/api/v2/` in M1 |

## Missing Components (to add in plan)

| Component | Milestone |
|-----------|-----------|
| `InvoiceModuleBase` shared mixin for revenue/procurement/invoice modules | M2 |
| Fair-queue per organization in worker | M1 |
| JSON schema validation for `module_plugin_config` | M1 |
| Visual regression testing | M2 |
| Module addition PR template ("no new router" check) | M3 |
| ADR-007: Generic Module Plugin Interface | M1 (doc) |

## Scalability Concerns

| Concern | Status in Plan |
|---------|----------------|
| 100+ modules UI | Addressed in M10 (search + categories) |
| Large file processing | Addressed in M1 (workers) |
| Multi-instance blob storage | Addressed in Wave 0 / M1 (S3/R2) |
| DB growth unbounded | Addressed in M10 (partitioning) |

## Security Concerns

| Concern | Status in Plan |
|---------|----------------|
| LLM in audit context | M4 human-in-the-loop mandatory |
| Client-side auth only | M7 server middleware |
| No rate limiting | M7 per-plan limits |
| PII to LLM | M4 redaction pipeline |

## Conflicts with Phase 1 / Phase 2 / Wave 0

| Area | Conflict | Resolution |
|------|----------|------------|
| Phase 2 analysis runs | Stub does not call rule engine | M1 `AnalysisEngine` replaces stub — **extends** Phase 2, no conflict |
| Phase 2 finding lifecycle | Works on shared `audit_findings` | Compatible; add `module_code` column |
| Phase 2 evidence/workpapers | Independent of module pipeline | No conflict |
| Phase 1 module catalog | DB catalog exists | GMMF extends with `module_plugin_config` |
| Phase 1 subscription gating | `enabled_module_codes` | Compatible with registry |
| Wave 0 stabilization | User states complete | Verify: S3, Redis, middleware, integration tests complete before M2 release |
| ADR-005 gradual API migration | v2 generic + legacy shims | Aligned |
| ADR-006 additive migrations | No destructive DDL | Aligned |

**No fundamental conflict** between Phase 3 design and Phase 1/2/Wave 0 — Phase 3 **extends** existing platform services.

---

## Recommendation: Ready for Implementation?

### Verdict: **READY FOR IMPLEMENTATION** with the following pre-M1 gates:

| Gate | Required | Status |
|------|----------|--------|
| Stakeholder approval of this document | Yes | Pending |
| Wave 0 deliverables verified (S3, Redis, workers, middleware, integration tests) | Yes | Stated complete — verify in M1 sprint 0 |
| ADR-007 (Plugin Interface) drafted | Yes | M1 week 1 |
| Business questions answered (LLM provider, Stripe, SSO IdP) | Before M4/M5/M7 | Open |
| Feature flag infrastructure | Before M2 release | M1 deliverable |

### Design changes required before coding: **None structural.**

Minor refinements expected during M1 as plugins are implemented — that is normal. The GMMF design is sound for 22–100+ modules.

---

## Final Recommendation: Phase 3 Milestone 2

### **Choose B: Migrate the three existing modules into the Generic Module Framework before building the remaining 19 modules.**

| Option | Recommendation |
|--------|----------------|
| A — Keep 3 separate, build 19 more | ❌ **Rejected** |
| B — Migrate 3, then build 19 on framework | ✅ **Approved approach** |

### Rationale

1. **72% duplicated pipeline** across 3 modules — migration cost is lowest now (3 modules, not 22).
2. **Platform shell already exists** (catalog, engagement enablement, analysis runs, finding lifecycle) — GMMF completes the missing engine layer.
3. **User experience unchanged** — migration is internal only.
4. Building 19 modules without framework would create **~15,000+ lines of copy-paste code** and make future migration **6–7× more expensive**.
5. Phase 2 **analysis runs** and **engagement hub** assume a unified module execution model — GMMF delivers that.
6. Tier 1 config-only modules (Compliance, Exception Report) become possible only with generic engines.

---

## Document Approval

| Role | Name | Date | Approved |
|------|------|------|----------|
| Product owner | | | ☐ |
| Tech lead | | | ☐ |
| Security / compliance | | | ☐ |

---

*This document supersedes informal architecture discussions and serves as the authoritative Phase 3 technical design. Update version history on each milestone completion.*
