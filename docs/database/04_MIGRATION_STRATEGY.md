# 04 — Migration Strategy

## Purpose

Define how AIML_AUDIT migrates from the current user-scoped analytics platform to multi-tenant SaaS **without renaming existing tables** and **without breaking** Journal, Revenue, or Procurement modules.

## Approved Principles

1. **Additive migrations only** — new tables and nullable columns
2. **No table renames**
3. **Keep `audit_projects`** temporarily for backward compatibility
4. **Dual-write / dual-read** during transition
5. **Strangler pattern** — new SaaS layer wraps existing APIs

See [../adr/ADR-006-Migration-Strategy.md](../adr/ADR-006-Migration-Strategy.md).

## Migration Phases Overview

| Phase | Focus | Schema impact |
|-------|-------|---------------|
| Phase 0 | Documentation & decisions | None |
| Phase 1 | Organizations + subscriptions + tenant FKs | New tables + nullable columns |
| Phase 2 | Module enablement + governance | New workflow tables |
| Phase 3 | Generic modules + scale | Optional refactor tables |

## Phase 1 — Database Migration Steps

### Step 1.1 — Platform tables (new)

```sql
-- Conceptual (not executed — documentation only)
CREATE subscription_plans (...);
CREATE organizations (...);
CREATE organization_subscriptions (...);
CREATE organization_members (...);
CREATE audit_module_catalog (...);  -- 22 rows seed
CREATE audit_logs (...);
```

### Step 1.2 — Tenant columns (additive)

```sql
ALTER TABLE clients ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE audit_engagements ADD COLUMN organization_id UUID;
-- Nullable during backfill; NOT NULL after validation
```

### Step 1.3 — Data backfill

| Source | Target |
|--------|--------|
| Each existing `users` row | One `organizations` row from `company_name` |
| User | `organization_members` role=owner |
| Each `clients.user_id` | Set `clients.organization_id` from user's org |

### Step 1.4 — Access control switch

- JWT adds `organization_id`
- Queries filter `organization_id` instead of `user_id`
- Keep `user_id` filter as fallback during dual-read window

### Step 1.5 — Catalog seed

Insert 22 modules into `audit_module_catalog` matching [../business/03_MODULE_CATALOG.md](../business/03_MODULE_CATALOG.md).

## Phase 2 — Module Enablement Migration

### Map legacy projects to enabled modules

| `audit_projects.project_type` | Catalog code |
|-------------------------------|--------------|
| `journal_testing` | `JOURNAL_ENTRY_TESTING` |
| `revenue_testing` | `REVENUE_TESTING` |
| `procurement_testing` | `PROCUREMENT_TESTING` |

For each existing project, create `engagement_enabled_modules` row on parent engagement.

**Do not delete** `audit_projects` — existing FKs from journal/revenue/procurement data depend on them.

## Phase 3 — Governance tables (additive)

```
workpapers, evidence, evidence_links,
review_comments, approvals,
finding_status_history, module_analysis_runs,
usage_records, report_history
```

## API Migration (Coordinated, Not Immediate)

| Stage | Behavior |
|-------|----------|
| Now | Keep `/upload`, `/revenue/*`, `/procurement/*` |
| Phase 2 | Add `/engagements/{id}/modules` enablement APIs |
| Phase 3 | Introduce `/modules/{code}/*` parallel to legacy |
| Phase 3+ | Deprecate legacy prefixes with sunset headers |

## Frontend Migration

| Stage | Change |
|-------|--------|
| Phase 1 | Org context in session; firm admin pages |
| Phase 2 | Engagement hub; hide standalone Projects nav |
| Phase 3 | Remove workstreams panel; catalog driven by API |

## Rollback Strategy

- Feature flags for org-scoped queries
- If Phase 1 fails: revert JWT claims; ignore `organization_id` columns
- Migrations are forward-only (Alembic downgrade scripts optional for dev)

## Testing Requirements Before Cutover

- [ ] Firm A user cannot read Firm B client by UUID
- [ ] Two users in same firm see same clients
- [ ] Existing demo login still works after backfill
- [ ] All three module upload/analysis flows unchanged
- [ ] Subscription limit blocks upload when exceeded

## Risks

| Risk | Mitigation |
|------|------------|
| Incomplete backfill | Validation query: clients with NULL organization_id |
| Production demo data | Run backfill in Railway before cutover |
| Long migration lock | Batch backfill off-peak |

## Recommendations

1. Run Phase 1 on staging with copy of production DB
2. Document dual-read window duration (suggest 2 sprints max)
3. Never drop `user_id` on clients until Phase 2 complete

---

*Related: [../roadmap/PHASE1_SAAS_FOUNDATION.md](../roadmap/PHASE1_SAAS_FOUNDATION.md)*
