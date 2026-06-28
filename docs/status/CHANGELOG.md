# Changelog

All notable changes to the AIML_AUDIT platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) where applicable.

---

## [Unreleased]

### Added
- Complete enterprise SaaS documentation pack (31 markdown files)
  - Architecture docs (6): system, SaaS, multi-tenant, navigation, user flow, folder structure
  - Database docs (4): design, ER diagram, relationships, migration strategy
  - API docs (3): architecture, existing APIs, future generic module API
  - Business docs (4): subscription, organization, module catalog, engagement model
  - Roadmap docs (5): Phase 0–3, implementation roadmap
  - ADRs (6): organizations, module catalog, tenant isolation, module enablement, API strategy, migration strategy
  - Status docs (3): project status, changelog, next steps
- Enterprise SaaS Architecture Review (`docs/ENTERPRISE_SAAS_ARCHITECTURE_REVIEW.md`)

### Planned (Phase 1 — not yet implemented)
- Multi-tenant organizations and subscription plans
- Module catalog in PostgreSQL
- Tenant isolation via `organization_id`
- Audit logging

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
