# Project Status — AIML_AUDIT

**Last updated:** June 7, 2026  
**Branch:** `architecture`  
**Latest commit:** `7f468d6`

---

## Current Version

| Component | Version |
|-----------|---------|
| Backend API | 2.0.0 |
| Frontend | Next.js 14 (App Router) |
| Database migrations | 001–006 (Alembic) |
| Documentation | Phase 0 complete |

### Production URLs

| Service | URL |
|---------|-----|
| Frontend | https://auditai-login.vercel.app |
| Backend API | https://aiml-audit-api-production.up.railway.app |
| API Docs | https://aiml-audit-api-production.up.railway.app/docs |
| Demo login | `auditor@demo.auditai.com` / `AuditAI2026!` |

---

## Completed Features

### Authentication & Users
- JWT access + refresh token flow
- User registration, login, logout, profile (`/auth/me`)
- Roles stored: `auditor`, `partner`, `manager`, `admin` (not enforced on API)

### Client & Engagement Hierarchy
- Full CRUD for clients, engagements, projects
- Hierarchy: User → Clients → Engagements → Projects

### Audit Modules (End-to-End)
| Module | Rules | Upload | Risk | Findings | Reports | Frontend |
|--------|-------|--------|------|----------|---------|----------|
| Journal Entry Testing | 7 | ✓ | ✓ | ✓ | ✓ | ✓ |
| Revenue Testing | 7 | ✓ | ✓ | ✓ | — | ✓ |
| Procurement Testing | 7 | ✓ | ✓ | ✓ | — | ✓ |

### Rule Engine
- 21 rules across 3 modules (`rules_master` table)
- Configurable thresholds per engagement (`large_value_threshold`)
- Rules Edit UI in dashboard

### Dashboard & Analytics
- KPI dashboard with engagement metrics
- Risk score visualization
- Findings summary

### Deployment
- Vercel (frontend) + Railway (backend + PostgreSQL)
- CORS configured for production domains
- Demo hierarchy auto-seeded on startup

### Documentation (Phase 0)
- 31 markdown documents across 7 folders
- 6 Architecture Decision Records
- Enterprise SaaS Architecture Review

---

## Pending Features

### Phase 1 — SaaS Foundation
- [ ] `organizations` and `organization_members` tables
- [ ] `subscription_plans` and billing limits
- [ ] `organization_id` tenant isolation
- [ ] Module catalog in PostgreSQL (22 modules)
- [ ] Per-engagement module enablement
- [ ] Audit logging
- [ ] Team user invitation
- [ ] JWT `org_id` claim

### Phase 2 — Enterprise Workflow
- [ ] Engagement team assignment
- [ ] Evidence repository + blob storage
- [ ] Workpapers
- [ ] Finding lifecycle (Open → Review → Cleared)
- [ ] Review comments and partner approval
- [ ] Async analysis jobs
- [ ] Consolidated engagement reports

### Phase 3 — AI & Scale
- [ ] Generic `/modules/{code}/*` API
- [ ] Modules 4–22 implementation
- [ ] LLM narratives and AI credits
- [ ] MFA / SSO
- [ ] Stripe billing automation
- [ ] Usage metering

---

## Architecture Decisions

| ADR | Decision | Status |
|-----|----------|--------|
| [ADR-001](../adr/ADR-001-Organizations.md) | Organizations as tenant root | Accepted |
| [ADR-002](../adr/ADR-002-Module-Catalog.md) | Module catalog in PostgreSQL | Accepted |
| [ADR-003](../adr/ADR-003-Tenant-Isolation.md) | Tenant isolation via organization_id | Accepted |
| [ADR-004](../adr/ADR-004-Module-Enablement.md) | Per-engagement module enablement | Accepted |
| [ADR-005](../adr/ADR-005-API-Strategy.md) | Gradual generic module API migration | Accepted |
| [ADR-006](../adr/ADR-006-Migration-Strategy.md) | Additive-only migrations | Accepted |

---

## Current Database

**17 tables** in PostgreSQL:

| Table | Purpose |
|-------|---------|
| `users` | Auditor accounts |
| `refresh_tokens` | JWT refresh rotation |
| `clients` | Auditee companies |
| `audit_engagements` | FY audit assignments |
| `audit_projects` | Module work containers |
| `journal_entries` | JE module data |
| `journal_rule_results` | JE rule output |
| `journal_risk_scores` | JE risk scores |
| `revenue_transactions` | Revenue module data |
| `revenue_rule_results` | Revenue rule output |
| `revenue_risk_scores` | Revenue risk scores |
| `procurement_invoices` | Procurement module data |
| `procurement_rule_results` | Procurement rule output |
| `procurement_risk_scores` | Procurement risk scores |
| `audit_findings` | Cross-module findings |
| `reports` | Generated report files |
| `rules_master` | Configurable rule definitions |

**Missing for SaaS:** organizations, subscriptions, module catalog, audit logs, evidence, workpapers.

---

## Current APIs

**13 routers**, ~40 endpoints. See [02_EXISTING_APIS.md](../api/02_EXISTING_APIS.md).

| Router | Prefix |
|--------|--------|
| health | `/health` |
| auth | `/auth` |
| clients | `/clients` |
| engagements | `/engagements` |
| projects | `/projects` |
| upload + journal analytics | `/upload`, `/run-rules`, … |
| revenue | `/revenue` |
| procurement | `/procurement` |
| rules | `/rules` |
| rules_master | `/rules-master` |
| dashboard | `/dashboard` |
| analytics/reports | `/reports` |

---

## Current Modules

### Built (3)
1. Journal Entry Testing — `journal_testing`
2. Revenue Testing — `revenue_testing`
3. Procurement Testing — `procurement_testing`

### Catalog (frontend only, 20 listed)
Remaining 17 modules marked `coming_soon` in `lib/dashboard/modules.ts`. Target catalog: **22 modules** (see [03_MODULE_CATALOG.md](../business/03_MODULE_CATALOG.md)).

---

## Readiness Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| **SaaS Readiness** | 24/100 | No multi-tenancy, subscriptions, or org model |
| **Enterprise Readiness** | 39/100 | Strong analytics; weak workflow, governance, AI |
| **Module Coverage** | 14% | 3 of 22 modules built |
| **Documentation** | 95/100 | Phase 0 complete; pending implementation |

### SaaS Blockers
1. `Client.user_id == current_user.id` — user-scoped, not firm-scoped
2. No `organizations` table
3. No subscription enforcement
4. Module catalog not in database
5. No audit trail / compliance logging

### Enterprise Blockers
1. No evidence or workpaper management
2. No review/approval workflow
3. No async job processing for large datasets
4. Reports stored locally (lost on redeploy)
5. Roles defined but not enforced

---

## Technical Debt

| Item | Severity | Phase to address |
|------|----------|------------------|
| Duplicated module API prefixes | Medium | Phase 3 |
| 3 duplicated frontend workspaces | Medium | Phase 2–3 |
| User-scoped access control | **Critical** | Phase 1 |
| Frontend module catalog hardcoded | High | Phase 1 |
| No Next.js auth middleware on `/dashboard/*` | High | Phase 1 |
| Reports on local filesystem | Medium | Phase 2 |
| Forgot-password stub (no email) | Low | Phase 2 |
| Default JWT secret warning in prod logs | Medium | Phase 1 |

---

## Next Recommended Task

**Await stakeholder approval**, then begin **Phase 1: SaaS Foundation**:

1. Create Alembic migration 007: `organizations`, `organization_members`, `subscription_plans`
2. Add nullable `organization_id` to `clients` and `audit_engagements`
3. Implement `TenantContext` and update `project_access.py`
4. Backfill existing users → organizations

See [NEXT_STEPS.md](./NEXT_STEPS.md) for full task breakdown.

---

*Documentation index: [../README.md](../README.md)*
