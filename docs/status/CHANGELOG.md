# Changelog

All notable changes to the AIML_AUDIT platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) where applicable.

---

## [Unreleased]

### Added — Wave 0 Milestone 2: Phase 2 Enterprise Workflow
- Analysis run lifecycle API: submit-review, approve, return, designate-official, archive
- Locked/archived run mutation guards (`run_lock_guard.py`) on evidence, workpapers, findings
- Auto-workspace: audit project + draft analysis run created when module enabled on engagement
- Cross-module `finding_relationships` table (migration 021) + CRUD API
- Fixed consolidated report `save_report_artifact` import in `engagement_hub_service.py`
- Engagement hub UI: official runs panel, lifecycle action buttons, status badges
- Frontend API helpers for run lifecycle and finding relationships
- Tests: `backend/tests/test_wave0_m2_phase2.py`

### Added — Wave 0 Milestone 3: Refactoring
- Shared `handle_service_error()` in `backend/app/routers/errors.py`

### Added — Wave 0 Milestone 4: Testing
- HTTP integration tests: `backend/tests/test_wave0_m4_integration.py`
- Added `httpx` test dependency

### Added — Wave 0 Milestone 5–6: Documentation
- `WAVE0_M2`–`M5` milestone reports and `WAVE0_COMPLETION_REPORT.md`
- Updated `PROJECT_STATUS.md`

### Added — Wave 0 Milestone 1: Phase 1 Closeout
- Registration auto-creates organization, owner membership, and Free subscription plan
- Demo user seeded with `Demo Audit Firm` organization; clients/engagements backfilled with `organization_id`
- Next.js `middleware.ts` protects `/dashboard/*` via session cookie
- Org-scoped client list/access (removed `user_id` OR fallback when tenant has organization)
- Audit logs on organization create/update/close, member invite/update/remove, subscription plan change
- Removed orphan `app/api/auth/register` stub route
- Tests: `backend/tests/test_wave0_m1_phase1.py`

### Added — Phase 1 Milestone 3: Organization Members
- Alembic migration `009_organization_members.py`: `organization_members` table
- Eight org-scoped roles with RBAC permission matrix (`member_constants.py`, `require_org_permission` in deps)
- Member repository, service, schemas, `/organizations/*/members/*` router
- Invite by email (creates user if needed), change roles, remove/disable members
- Owner membership on org create; backfill owners from existing `default_organization_id`
- Frontend `OrganizationMembers` on Settings page
- Invited memberships activated on login/refresh
- User usage count uses active `organization_members`
- Unit tests: `backend/tests/test_organization_members.py` (8 tests)

### Added — Phase 1 Milestone 2: Subscription Plans
- Alembic migration `008_subscription_plans.py`: `subscription_plans`, `organization_subscriptions`
- Seed plans: Free, Starter, Professional, Enterprise with usage limits
- Subscription repository, service, schemas, `/subscriptions/*` router
- Auto-assign Free plan when organization is created; backfill existing orgs in migration
- Frontend `SubscriptionSettings` on Settings page (usage vs limits, plan switch)
- Unit tests: `backend/tests/test_subscriptions.py` (5 tests)

### Added — Phase 1 Milestone 1: Organizations
- Alembic migration `007_organizations.py`: `organizations` table + `users.default_organization_id`
- `Organization` SQLAlchemy model with status check constraint and JSONB settings
- Organization repository, service, Pydantic schemas, and `/organizations/*` router
- Frontend `OrganizationSettings` component on Settings page
- API client: `fetchMyOrganization`, `createOrganization`, `updateMyOrganization`
- Unit tests: `backend/tests/test_organizations.py` (8 tests)

### Added (documentation)
- Complete enterprise SaaS documentation pack (31 markdown files)
  - Architecture docs (6): system, SaaS, multi-tenant, navigation, user flow, folder structure
  - Database docs (4): design, ER diagram, relationships, migration strategy
  - API docs (3): architecture, existing APIs, future generic module API
  - Business docs (4): subscription, organization, module catalog, engagement model
  - Roadmap docs (5): Phase 0–3, implementation roadmap
  - ADRs (6): organizations, module catalog, tenant isolation, module enablement, API strategy, migration strategy
  - Status docs (3): project status, changelog, next steps
- Enterprise SaaS Architecture Review (`docs/ENTERPRISE_SAAS_ARCHITECTURE_REVIEW.md`)

### Planned (Phase 1 — remaining milestones)
- Tenant isolation (Milestone 4)
- Tenant isolation via `organization_id` (Milestone 4)
- Module catalog in PostgreSQL (Milestone 5)

---

## [2.0.0] — 2026-06

### Added
- **Revenue Testing module** — full stack
  - Backend: `/revenue/*` endpoints (upload, run-rules, run-risk, risk-scores, findings)
  - 7 revenue rules (`REV_*`) in rules engine
  - Frontend: enterprise workspace at `/dashboard/ai-modules/revenue-testing`
  - Sample data: revenue transaction Excel template
  - Alembic migration `005_revenue_testing.py`

- **Procurement Testing module** — full stack
  - Backend: `/procurement/*` endpoints
  - 7 procurement rules (`PROC_*`) in rules engine
  - Frontend: enterprise workspace at `/dashboard/ai-modules/procurement-testing`
  - Sample data: `database/sample_procurement_invoices.xlsx`
  - Alembic migration `006_procurement_testing.py`

- Revenue and Procurement data models (`revenue_transactions`, `procurement_invoices`, rule results, risk scores)

### Fixed
- Procurement workspace client-side crash caused by incorrect icon mapping in `EnterpriseCapabilitiesPanel.tsx`

### Changed
- API version bumped to 2.0.0
- Module workstreams separated from Journal Entry Testing

---

## [1.2.0] — 2026-05

### Added
- Vercel production deployment configuration (frontend)
- Railway production deployment configuration (backend + PostgreSQL)
- CORS settings for production domains
- Demo hierarchy auto-seed on application startup

### Changed
- Engagement workstreams separated from Journal Entry Testing UI
- Project types: `journal_testing`, `revenue_testing`, `procurement_testing`

---

## [1.1.0] — 2026-05

### Added
- Audit hierarchy architecture: Clients → Engagements → Projects
- Rules Edit UI in dashboard
- `rules_master` table with configurable rule definitions
- Alembic migrations 002–004 (engagements, projects, rules master)
- Dashboard analytics endpoints

### Changed
- Data model restructured from flat user-projects to full audit hierarchy

---

## [1.0.0] — 2026-04

### Added
- Initial AIML Audit platform release
- **Journal Entry Testing module**
  - Excel upload, 7 journal rules, risk scoring, findings generation
  - Report generation (Excel, PDF, working paper)
- JWT authentication with refresh tokens
- User registration and login
- Client CRUD
- FastAPI backend with PostgreSQL
- Next.js 14 frontend with dashboard
- Alembic migration 001 (initial schema)
- Sample journal entries file

### Infrastructure
- Git repository initialized
- Backend environment configuration
- `.gitignore` for Python and Node patterns

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| Unreleased | 2026-06 | Documentation pack, SaaS architecture blueprint |
| 2.0.0 | 2026-06 | Revenue + Procurement modules, API v2 |
| 1.2.0 | 2026-05 | Production deployment (Vercel + Railway) |
| 1.1.0 | 2026-05 | Audit hierarchy, rules master, dashboard |
| 1.0.0 | 2026-04 | Journal Entry Testing MVP |

---

*For current status see [PROJECT_STATUS.md](./PROJECT_STATUS.md)*
