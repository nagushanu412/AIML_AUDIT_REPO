# ADR-006: Additive Database Migration Strategy

## Status

**Accepted** — June 2026

## Context

Production database on Railway contains demo and pilot data across 17 tables with 6 Alembic migrations (001–006). SaaS transformation requires new tables (`organizations`, `subscription_plans`, `audit_module_catalog`, etc.) and new columns (`organization_id` on `clients`, `audit_engagements`).

Renaming or dropping existing tables would break the 3 working audit modules and require coordinated frontend/backend downtime.

## Decision

Use **additive-only migrations**:

1. **CREATE** new tables; never DROP existing tables in Phase 1–2
2. **ADD** nullable columns first; backfill; then ADD NOT NULL constraint in separate migration
3. **KEEP** `audit_projects` and all module-specific data tables unchanged
4. **BACKFILL** script: each existing user → new organization; copy `user_id` ownership to `organization_id`
5. **Alembic** remains migration tool; one migration per logical change
6. **No table renames** until Phase 3 generic API is stable

Rollback strategy: new columns/tables can be ignored by old code; feature flag `USE_ORG_TENANCY` controls which code path runs.

## Consequences

### Positive

- Zero downtime deployment possible
- Existing Journal/Revenue/Procurement flows unaffected during migration
- Rollback = disable feature flag, not database restore
- Clear audit trail via Alembic version history

### Negative

- Temporary schema complexity (old + new columns coexist)
- Backfill must be idempotent and tested on staging clone
- Discipline required to avoid destructive migrations under pressure

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| Greenfield database | Loses production data; duplicate ops burden |
| Big-bang schema rewrite | Unacceptable downtime and regression risk |
| Rename clients → organizations | Wrong semantics; clients are auditees |
| Manual SQL without Alembic | No version tracking; team coordination failure |

## Related Documents

- [../database/04_MIGRATION_STRATEGY.md](../database/04_MIGRATION_STRATEGY.md)
- [../database/01_DATABASE_DESIGN.md](../database/01_DATABASE_DESIGN.md)
- [../roadmap/PHASE1_SAAS_FOUNDATION.md](../roadmap/PHASE1_SAAS_FOUNDATION.md)
