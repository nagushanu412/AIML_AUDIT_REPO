# ADR-002: Module Catalog in PostgreSQL

## Status

**Accepted** — June 2026

## Context

AIML_AUDIT offers 22 AI audit modules (Journal Entry Testing, Revenue Testing, Procurement Testing, and 19 planned modules). Currently:

- **3 modules** are fully implemented end-to-end (backend rules, upload, risk, findings)
- **20 modules** are listed in frontend `lib/dashboard/modules.ts` with hardcoded status
- Module enablement per engagement is not persisted
- Subscription plans cannot gate module access

The business requires ONE master catalog where modules are standard products—not separate workstreams—and engagements enable only required modules.

## Decision

Store the module catalog in PostgreSQL as `audit_module_catalog` with seed data for all 22 modules. Track per-engagement enablement in `engagement_enabled_modules`. Subscription plans reference allowed modules via `subscription_plan_modules` (or JSONB `enabled_modules` on plan row).

Frontend `modules.ts` becomes a **read-through cache** of API data, not the source of truth.

## Consequences

### Positive

- Single source of truth for module metadata (name, code, category, status)
- Subscription and engagement gating enforced server-side
- New modules added via migration seed + plugin registration
- Consistent module list across web, API, and future mobile clients

### Negative

- Initial seed migration required for 22 modules
- Frontend must fetch catalog on load (cache strategy needed)
- Module `status` transitions (planned → beta → active) require DB updates

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| Keep frontend-only catalog | Cannot enforce subscription limits; drift between UI and backend |
| JSON config file in repo | No runtime updates; no per-org overrides |
| Separate microservice for catalog | Over-engineered for 22 static modules |
| One table per module type | Does not scale to 22 modules; duplicates schema |

## Related Documents

- [../business/03_MODULE_CATALOG.md](../business/03_MODULE_CATALOG.md)
- [ADR-004-Module-Enablement.md](./ADR-004-Module-Enablement.md)
- [../api/03_FUTURE_GENERIC_MODULE_API.md](../api/03_FUTURE_GENERIC_MODULE_API.md)
