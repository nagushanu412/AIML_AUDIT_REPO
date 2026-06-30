# 01 — Database Design

## Purpose

Document the current PostgreSQL schema, design principles, indexes, and the target SaaS schema extensions.

## Current Design Principles

- Single schema (`public`) in PostgreSQL
- SQLAlchemy ORM models in one file: `backend/app/models/audit.py`
- Alembic for migrations (7 versions: 001–007)
- JSONB for flexible rule config and finding entity references
- Cascade deletes from engagement → project → transactional data

## Current Tables (18)

| # | Table | Primary purpose |
|---|-------|-----------------|
| 1 | `users` | Identity, role string, profile, `default_organization_id` (interim) |
| 2 | `organizations` | Audit firm tenant *(Phase 1 M1)* |
| 3 | `refresh_tokens` | JWT refresh rotation |
| 4 | `clients` | Audited entities (`user_id` owner) |
| 5 | `audit_engagements` | FY engagements per client |
| 6 | `audit_projects` | Module instance via `project_type` |
| 7 | `journal_entries` | JE upload population |
| 8 | `rules_master` | Global rule definitions |
| 9 | `rule_results` | Journal rule violations |
| 10 | `risk_scores` | Journal entry scores |
| 11 | `audit_findings` | Aggregated findings (all modules) |
| 12 | `reports` | Export file metadata |
| 13 | `revenue_invoices` | Revenue upload population |
| 14 | `revenue_rule_results` | Revenue rule violations |
| 15 | `revenue_risk_scores` | Revenue invoice scores |
| 16 | `procurement_invoices` | Procurement upload population |
| 17 | `procurement_rule_results` | Procurement rule violations |
| 18 | `procurement_risk_scores` | Procurement invoice scores |

## Migration History

| Version | File | Summary |
|---------|------|---------|
| 001 | `001_initial_schema.py` | users, journal_entries, rules, findings |
| 002 | `002_hierarchy_and_rules.py` | clients, engagements, projects, rules_master seed |
| 003 | `003_refresh_tokens.py` | refresh token table |
| 004 | `004_rule_config_defaults.py` | rule config_schema backfill |
| 005 | `005_revenue_testing.py` | revenue tables + REV_* rules |
| 006 | `006_procurement_testing.py` | procurement tables + PROC_* rules |
| 007 | `007_organizations.py` | organizations + users.default_organization_id |

### `organizations` (Milestone 1)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `name` | varchar(255) | Firm legal/trading name |
| `slug` | varchar(100) UK | URL-safe unique identifier |
| `status` | varchar(50) | `active`, `suspended`, `closed` |
| `settings` | JSONB | Timezone, branding, defaults |
| `created_at`, `updated_at` | timestamptz | |

## Key Columns

### `audit_projects.project_type`

Values in use: `journal_testing`, `revenue_testing`, `procurement_testing`

### `audit_findings.journal_entry_ids`

JSONB array of UUIDs — stores journal entry IDs **or** invoice IDs (revenue/procurement). Naming debt.

### `rules_master`

Global table; 21 rule codes across JE + revenue + procurement. Configurable via `config_schema` JSONB.

## Indexes (from migrations)

- `users.email` (unique)
- `clients.user_id`
- `audit_engagements.client_id`
- `audit_projects.engagement_id`
- `journal_entries.project_id`, `posting_date`
- `rule_results.project_id`
- `risk_scores.project_id` (+ unique project+entry)
- `audit_findings.project_id`
- `reports.project_id`
- Revenue/procurement invoice `project_id`

**Gaps:** No index on `rule_code`, `risk_category`, `procurement_rule_results.project_id`

## Current Implementation

- Connection pool: `pool_size=5`, `max_overflow=10`
- No row-level security (RLS) in PostgreSQL
- Tenant isolation via application code only

## Future Design (Additive)

See [02_ER_DIAGRAM.md](./02_ER_DIAGRAM.md) and approved decisions:

| New table group | Purpose |
|-----------------|---------|
| Platform | `subscription_plans`, `organization_subscriptions` |
| Tenancy | `organizations`, `organization_members` |
| Catalog | `audit_module_catalog`, `engagement_enabled_modules` |
| Governance | `audit_logs`, `workpapers`, `evidence`, `review_comments`, `approvals` |
| Operations | `module_analysis_runs`, `usage_records`, `report_history` |

### Additive column changes

- `clients.organization_id`
- `audit_engagements.organization_id`
- `audit_findings.status`, `module_code`, `organization_id`
- `rules_master.organization_id` (nullable)

## Advantages (Current)

- Normalized analytics schema
- Clear project-scoped data for three modules
- Migration chain is linear and reproducible

## Disadvantages (Current)

- No tenant column — SaaS blocker
- Per-module table triplication (journal/revenue/procurement)
- Global rules_master shared across all users
- `audit_projects` conflicts with engagement-enabled modules target

## Migration Strategy

**Additive only. No table renames.**

1. New SaaS tables (no changes to existing)
2. Nullable FKs + backfill
3. Dual-write period
4. Deprecate `user_id` on clients (do not drop in Phase 1)

See [04_MIGRATION_STRATEGY.md](./04_MIGRATION_STRATEGY.md).

## Risks

| Risk | Impact |
|------|--------|
| 22 modules = 22 table groups | Schema sprawl |
| Finding ID field misuse | Reporting errors |
| Missing tenant index | Slow queries at scale |

## Recommendations

1. Introduce `audit_module_catalog` before module #4
2. Add generic `affected_entity_ids` on findings (keep old column)
3. Plan module data abstraction before building modules 4–10

---

*Related: [03_TABLE_RELATIONSHIPS.md](./03_TABLE_RELATIONSHIPS.md)*
