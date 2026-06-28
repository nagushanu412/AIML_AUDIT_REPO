# Phase 1 — SaaS Foundation

## Purpose

Establish multi-tenant foundation: organizations, subscriptions, tenant isolation, module catalog in DB, and audit logging.

## Duration (Estimate)

10–14 weeks

## Prerequisites

- Phase 0 documentation approved
- ADRs 001, 003, 006 accepted

## Goals

1. Safe multi-tenant data isolation for pilot audit firms
2. Multiple users per organization sharing clients
3. Subscription plan enforcement (manual billing OK)
4. Module catalog in PostgreSQL (22 modules)
5. No regression to Journal, Revenue, Procurement modules

## Database Deliverables

| Item | Type |
|------|------|
| `organizations` | New table |
| `organization_members` | New table |
| `subscription_plans` | New table + seed 4 plans |
| `organization_subscriptions` | New table |
| `audit_module_catalog` | New table + seed 22 modules |
| `engagement_enabled_modules` | New table |
| `audit_logs` | New table |
| `clients.organization_id` | Additive column |
| `audit_engagements.organization_id` | Additive column |

## Backend Deliverables

| Item | Description |
|------|-------------|
| TenantContext service | Resolve org from JWT |
| Update `project_access` | Org-scoped checks |
| JWT claims | Add `org_id`, `member_role` |
| `/organizations/*` | CRUD + members invite |
| `/modules/catalog` | List catalog from DB |
| `/engagements/{id}/modules` | Enable/disable modules |
| Subscription middleware | Enforce max users/clients |
| Audit log middleware | Log mutations |
| Data backfill script | Existing users → orgs |

## Frontend Deliverables

| Item | Description |
|------|-------------|
| Registration creates org | Owner membership |
| Org context in session | Display firm name |
| Firm admin: invite user | Basic UI |
| Next.js middleware | Protect `/dashboard/*` |
| Engagement module enablement UI | Basic |
| Remove hardcoded subscription valid | Check API |

## Testing Deliverables

- Tenant isolation integration tests (Firm A ≠ Firm B)
- Two users same firm share clients test
- Regression: 3 module upload/analysis E2E
- Subscription limit tests

## Exit Criteria

- [ ] Two auditors at same firm see identical client list
- [ ] Firm A token cannot access Firm B resources by UUID
- [ ] Catalog served from API with 22 modules
- [ ] Demo account migrated to org model
- [ ] All Phase 1 endpoints write audit_logs

## Out of Scope (Phase 1)

- Stripe billing
- Workpapers / evidence
- Review / approval workflow
- Generic module API
- MFA / SSO

## Risks

| Risk | Mitigation |
|------|------------|
| Production data migration | Staging rehearsal |
| Dual model confusion | Documentation + UI labels |

## Recommendations

- Feature flag `USE_ORG_TENANCY` for gradual rollout
- Keep demo login working throughout migration

---

*Related: [PHASE2_ENTERPRISE_WORKFLOW.md](./PHASE2_ENTERPRISE_WORKFLOW.md)*
