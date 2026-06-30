# Project Status — AIML_AUDIT

**Last updated:** June 7, 2026  
**Branch:** `architecture` (local — Milestones 1–3 uncommitted)  
**Phase 1:** Milestone 3 (Organization Members) implemented locally

---

## Current Version

| Component | Version |
|-----------|---------|
| Backend API | 2.0.0 |
| Frontend | Next.js 14 (App Router) |
| Database migrations | 001–009 (Alembic) — **009 requires `alembic upgrade head`** |
| Documentation | Phase 0 complete; Phase 1 M1–M3 in progress |

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

### Phase 1 Milestone 1 — Organizations *(local)*
- [x] `organizations` table (Alembic 007)
- [x] `users.default_organization_id` interim link (kept alongside `organization_members`)
- [x] Organization CRUD API (`/organizations/*`)
- [x] Organization service, repository, validation
- [x] Settings UI: create and edit audit firm profile
- [ ] Registration auto-creates org — Milestone 9

### Phase 1 Milestone 2 — Subscription Plans *(local)*
- [x] `subscription_plans` table + seed (Free, Starter, Professional, Enterprise)
- [x] `organization_subscriptions` table
- [x] Usage limits on plans (users, clients, engagements, storage, uploads, reports, AI credits)
- [x] Auto-assign Free plan on organization create
- [x] Backfill Free plan for existing organizations (migration 008)
- [x] Subscription API (`/subscriptions/*`)
- [x] Settings UI: plan display, usage vs limits, manual plan switch
- [ ] Subscription limit enforcement on APIs — Milestone 8

### Phase 1 Milestone 3 — Organization Members *(local)*
- [x] `organization_members` table (Alembic 009)
- [x] Eight org roles with RBAC permission matrix foundation
- [x] Invite users by email (existing or new account)
- [x] Remove/disable members, change roles
- [x] Owner membership on org create; backfill from `default_organization_id`
- [x] Member API (`/organizations/*/members/*`)
- [x] Settings UI: team member list, invite, role change, remove
- [x] Invited members activated on login
- [x] User count in subscription usage uses `organization_members`

---

## Pending Features

### Phase 1 — SaaS Foundation (remaining milestones)
- [x] `organizations` table *(Milestone 1)*
- [x] `subscription_plans` + `organization_subscriptions` *(Milestone 2)*
- [x] `organization_members` table *(Milestone 3)*
- [ ] `organization_id` tenant isolation *(Milestone 4)*
- [ ] Module catalog in PostgreSQL (22 modules) *(Milestone 5)*
- [ ] Per-engagement module enablement *(Milestone 6)*
- [ ] Audit logging *(Milestone 7)*
- [ ] Subscription enforcement *(Milestone 8)*
- [ ] Data backfill / migration *(Milestone 9)*
- [ ] End-to-end tenant tests *(Milestone 10)*
- [ ] JWT `org_id` claim *(Milestone 4)*

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

**20 tables** in PostgreSQL (after migration 008):

| Table | Purpose |
|-------|---------|
| `users` | Auditor accounts (+ `default_organization_id` interim link) |
| `organizations` | Audit firm tenant entity *(Milestone 1)* |
| `subscription_plans` | SaaS plan definitions *(Milestone 2)* |
| `organization_subscriptions` | Org ↔ plan assignment *(Milestone 2)* |
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

**Missing for SaaS:** tenant isolation on data tables, module catalog, audit logs, evidence, workpapers, usage_records.

---

## Current APIs

**15 routers**, ~49 endpoints. See [02_EXISTING_APIS.md](../api/02_EXISTING_APIS.md).

| Router | Prefix |
|--------|--------|
| health | `/health` |
| auth | `/auth` |
| organizations | `/organizations` *(Milestone 1)* |
| subscriptions | `/subscriptions` *(Milestone 2)* |
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
| **SaaS Readiness** | 32/100 | Organizations + subscription plans; no tenant isolation yet |
| **Enterprise Readiness** | 39/100 | Strong analytics; weak workflow, governance, AI |
| **Module Coverage** | 14% | 3 of 22 modules built |
| **Documentation** | 95/100 | Phase 0 complete; pending implementation |

### SaaS Blockers
1. `Client.user_id == current_user.id` — user-scoped, not firm-scoped *(Milestone 4)*
2. ~~No `organizations` table~~ — **resolved in Milestone 1 (local)**
3. ~~No subscription enforcement~~ — plans defined *(Milestone 2)*; API enforcement in Milestone 8
4. Module catalog not in database *(Milestone 5)*
5. No audit trail / compliance logging *(Milestone 7)*
6. No `organization_id` on clients/engagements — tenant isolation pending *(Milestone 4)*

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

**Next:** Begin **Milestone 4 — Tenant Isolation** (`organization_id` on all tenant-scoped tables, JWT claims, middleware).

See [NEXT_STEPS.md](./NEXT_STEPS.md) for full task breakdown.

---

*Documentation index: [../README.md](../README.md)*
