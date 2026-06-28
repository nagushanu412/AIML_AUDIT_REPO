# ADR-003: Tenant Isolation via organization_id

## Status

**Accepted** — June 2026

## Context

Multi-tenant SaaS requires that Firm A cannot access Firm B's data—even by guessing UUIDs. Current implementation in `project_access.py` validates ownership via:

```
Client.user_id == current_user.id
```

This is user-scoped, not firm-scoped. A second auditor at the same firm sees zero clients. A malicious user with a valid token could potentially access another user's resources if they obtain a UUID.

Target: support 100–10,000+ audit firms with zero cross-tenant data leaks.

## Decision

Apply **shared-database, shared-schema multi-tenancy** with `organization_id` on all tenant-scoped tables. Every API query and mutation must filter by the authenticated user's current organization.

Implementation pattern:

1. JWT includes `org_id` and `member_role`
2. `TenantContext` middleware resolves org from token
3. All list/get/update/delete operations add `WHERE organization_id = :org_id`
4. Integration tests verify Firm A token cannot read Firm B resources

Row-level security (PostgreSQL RLS) is optional enhancement in Phase 3; application-layer checks are sufficient for Phase 1.

## Consequences

### Positive

- Industry-standard pattern; well understood by developers
- Single database simplifies operations and reporting
- Additive migration: nullable `organization_id` → backfill → NOT NULL
- Compatible with existing UUID primary keys

### Negative

- Every new table must include `organization_id` (discipline required)
- Forgotten filter = security vulnerability (mitigate with tests + code review)
- Platform-admin cross-tenant views need separate bypass role

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| Database per tenant | 10,000 databases impractical on Railway/single ops team |
| Schema per tenant | Migration complexity multiplied by tenant count |
| PostgreSQL RLS only | Harder to debug; still need org_id column; defer to Phase 3 |
| Application-level user_id only | Does not support team collaboration |

## Related Documents

- [../architecture/03_MULTI_TENANT_ARCHITECTURE.md](../architecture/03_MULTI_TENANT_ARCHITECTURE.md)
- [ADR-001-Organizations.md](./ADR-001-Organizations.md)
- [../database/04_MIGRATION_STRATEGY.md](../database/04_MIGRATION_STRATEGY.md)
