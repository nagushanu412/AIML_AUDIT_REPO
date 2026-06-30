# ADR-001: Organizations as Tenant Root

## Status

**Accepted** — June 2026  
**Implemented (Milestone 1):** June 2026 — `organizations` table, CRUD API, interim `users.default_organization_id` link

## Context

AIML_AUDIT serves audit firms (e.g., ABC & Co, Deloitte, EY) as customers. The current data model ties all clients to individual `users.id`, making it impossible for multiple auditors at the same firm to share clients, engagements, and findings. The platform must scale from 100 to 10,000+ firms with strict data isolation.

The target hierarchy is:

```
Platform → Subscription Plans → Organizations → Users → Clients → Engagements → Modules
```

## Decision

Introduce an `organizations` table as the **tenant root entity**. Every audit firm is an organization. Users belong to organizations via `organization_members`. All tenant-scoped resources (`clients`, `audit_engagements`, and downstream tables) will carry `organization_id` for isolation.

Registration will create an organization (using `company_name` from user profile) and assign the registering user as `owner`.

## Consequences

### Positive

- Multiple users per firm share the same client portfolio
- Subscription limits enforced at organization level
- Clear billing entity for future Stripe integration
- Aligns with industry-standard SaaS multi-tenancy patterns

### Negative

- Requires migration of existing demo/production data
- All access checks must be updated from user-scoped to org-scoped
- JWT must carry `org_id` claim; users in multiple orgs need org-switching (future)

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| Use `users.company_name` as implicit tenant | No FK integrity; duplicate firm names; no membership model |
| Use `clients` as tenant root | Clients are auditees, not audit firms; wrong semantic |
| Separate database per firm | Operationally expensive at 10,000 firms; over-engineered for current scale |
| Schema-per-tenant PostgreSQL | Complex migrations; harder to manage catalog and platform tables |

## Related Documents

- [../business/02_ORGANIZATION_MODEL.md](../business/02_ORGANIZATION_MODEL.md)
- [ADR-003-Tenant-Isolation.md](./ADR-003-Tenant-Isolation.md)
- [../roadmap/PHASE1_SAAS_FOUNDATION.md](../roadmap/PHASE1_SAAS_FOUNDATION.md)
