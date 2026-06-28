# ADR-004: Per-Engagement Module Enablement

## Status

**Accepted** — June 2026

## Context

Audit engagements vary in scope. A statutory audit of a manufacturing company may require Journal Entry Testing, Revenue Testing, and GST Mismatch Checking. A payroll-focused review may only need Payroll Audit Checking.

Currently, modules are accessed via separate frontend routes (`/journal-entry-testing`, `/revenue-testing`, `/procurement-testing`) tied to `audit_projects` with `project_type`. There is no concept of "this engagement has these modules enabled."

The approved model treats Journal Entry, Revenue, and Procurement as **catalog modules**, not separate architectural workstreams.

## Decision

1. **Engagement-level enablement:** `engagement_enabled_modules` junction table links `audit_engagement_id` to `audit_module_catalog.id`
2. **Keep `audit_projects` temporarily:** Each enabled module creates (or reuses) an `audit_project` with matching `project_type` for backward compatibility with existing upload/rules/risk APIs
3. **UI shows only enabled modules** on the engagement hub
4. **Subscription plan caps** which modules can be enabled (e.g., Free plan: 3 modules max)

Migration path: existing projects remain; new engagements explicitly enable modules from catalog.

## Consequences

### Positive

- Matches real audit scoping practice
- Reduces UI clutter (only relevant modules shown)
- Subscription upsell lever ("enable GST module on Professional plan")
- Preserves existing 3 module backends without rewrite

### Negative

- Dual model during transition (`engagement_enabled_modules` + `audit_projects`)
- Risk of orphaned projects if enablement toggled off
- Frontend must consolidate 3 duplicated workspaces eventually

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| One project per engagement (no module split) | Cannot run parallel module analyses with separate data schemas |
| Module enablement at client level | Wrong granularity; modules vary per engagement/year |
| Remove audit_projects immediately | Breaks 3 working modules; high regression risk |
| Auto-enable all plan modules | Ignores engagement scope; wastes storage/compute |

## Related Documents

- [../business/04_ENGAGEMENT_MODEL.md](../business/04_ENGAGEMENT_MODEL.md)
- [ADR-002-Module-Catalog.md](./ADR-002-Module-Catalog.md)
- [../roadmap/PHASE2_ENTERPRISE_WORKFLOW.md](../roadmap/PHASE2_ENTERPRISE_WORKFLOW.md)
