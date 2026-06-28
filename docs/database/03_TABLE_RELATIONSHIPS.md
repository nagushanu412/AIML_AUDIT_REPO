# 03 — Table Relationships

## Purpose

Detailed relationship reference: cardinalities, foreign keys, cascade behavior, and cross-module dependencies.

## Hierarchy Chain (Current)

```
users (1) ──→ (N) clients
clients (1) ──→ (N) audit_engagements
audit_engagements (1) ──→ (N) audit_projects
audit_projects (1) ──→ (N) [module data tables]
audit_projects (1) ──→ (N) audit_findings
audit_projects (1) ──→ (N) reports
```

## Module Data Relationships

### Journal Entry Testing

| Child table | FK | Parent | On delete |
|-------------|-----|--------|-----------|
| `journal_entries` | `project_id` | `audit_projects` | CASCADE |
| `rule_results` | `project_id`, `journal_entry_id` | project, entry | CASCADE |
| `risk_scores` | `project_id`, `journal_entry_id` | project, entry | CASCADE |

Unique: `(project_id, journal_entry_id)` on `risk_scores`

### Revenue Testing

| Child table | FK | Parent |
|-------------|-----|--------|
| `revenue_invoices` | `project_id` | `audit_projects` |
| `revenue_rule_results` | `project_id`, `revenue_invoice_id` | project, invoice |
| `revenue_risk_scores` | `project_id`, `revenue_invoice_id` | project, invoice |

### Procurement Testing

| Child table | FK | Parent |
|-------------|-----|--------|
| `procurement_invoices` | `project_id` | `audit_projects` |
| `procurement_rule_results` | `project_id`, `procurement_invoice_id` | project, invoice |
| `procurement_risk_scores` | `project_id`, `procurement_invoice_id` | project, invoice |

## Shared Findings Model

`audit_findings` is **shared** across all three modules:

- Scoped by `project_id`
- Grouped by `rule_code`
- `journal_entry_ids` JSONB holds affected entity UUIDs (misnamed for revenue/procurement)

**Regenerating findings deletes all prior findings for the project** (no history).

## Rules Master

| Relationship | Notes |
|--------------|-------|
| `rules_master` → `rule_results` | Logical via `rule_code`; no FK |
| Global scope | All tenants share same rules today |
| Seed | 7 JE rules in migration 002; REV/PROC in 005/006 |

## Reports

| Column | Relationship |
|--------|--------------|
| `project_id` | FK → audit_projects |
| `generated_by` | FK → users (nullable SET NULL) |
| `file_path` | Local filesystem path (not DB blob) |

## Auth Relationships

```
users (1) ──→ (N) refresh_tokens  [CASCADE delete]
```

## Access Path for Authorization (Current)

Every protected resource resolves:

```
entity → audit_projects → audit_engagements → clients → users.id
```

Implemented in `project_access.py`: `get_owned_project`, `get_owned_client`, `get_owned_engagement`.

## Target Relationships (Additional)

| Relationship | Cardinality |
|--------------|-------------|
| organizations ↔ users | N:M via `organization_members` |
| organizations → clients | 1:N |
| subscription_plans → organizations | 1:N via subscription |
| audit_engagements ↔ modules | N:M via `engagement_enabled_modules` |
| audit_engagements ↔ users | N:M via `engagement_team_members` |
| findings ↔ evidence | N:M via `evidence_links` |

## Current Implementation

- Strong CASCADE from project deletion (wipes all module data)
- No soft-delete on engagements or clients
- No orphan protection for cross-module references

## Future Design

- Soft-delete flags on clients/engagements for audit trail
- Finding history table instead of delete-on-regenerate
- FK from findings to `engagement_id` for cross-project queries

## Advantages

- Simple cascade simplifies demo reset
- Clear project boundary for analysis runs

## Disadvantages

- Delete project = irreversible data loss
- Shared findings table without `module_code` column today
- No engagement-level finding rollup without joining projects

## Migration Strategy

1. Add `organization_id` with FK to organizations on clients
2. Add `engagement_enabled_modules` without removing projects FK chain
3. Backfill enablement from existing projects per engagement

## Risks

Breaking CASCADE when adding soft-delete  
Orphan findings if project deprecated before migration completes

## Recommendations

- Add `module_code` and `engagement_id` to findings in Phase 1
- Document cascade behavior in admin UI before production firms

---

*Related: [01_DATABASE_DESIGN.md](./01_DATABASE_DESIGN.md)*
