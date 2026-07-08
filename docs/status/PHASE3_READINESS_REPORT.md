# Phase 3 Readiness Report — AIML_AUDIT

**Review date:** July 8, 2026  
**Branch:** `architecture` (latest commit: `07edc49` — Phase 2 router import fix)  
**Reviewer:** Lead software architect review (codebase + documentation audit)  
**Status:** Review complete — **awaiting stakeholder approval before Phase 3 implementation**

---

## Purpose

This document records a complete pre-Phase 3 review of the AIML_AUDIT platform. It validates compatibility between Phase 1, Phase 2, and planned Phase 3 work; identifies gaps and risks; lists clarification questions; and proposes an implementation sequence.

**No Phase 3 code, migrations, or refactors should begin until this report is approved and open questions are answered.**

### Source documents reviewed

| Document | Path | Notes |
|----------|------|-------|
| Phase 1 roadmap | [../roadmap/PHASE1_SAAS_FOUNDATION.md](../roadmap/PHASE1_SAAS_FOUNDATION.md) | `PHASE1_IMPLEMENTATION_GUIDE.md` does not exist |
| Phase 2 enterprise guide | [../roadmap/PHASE2_IMPLEMENTATION_GUIDE.md](../roadmap/PHASE2_IMPLEMENTATION_GUIDE.md) | Authoritative enterprise criteria |
| Phase 2 final report | [../roadmap/PHASE2_FINAL_IMPLEMENTATION_REPORT.md](../roadmap/PHASE2_FINAL_IMPLEMENTATION_REPORT.md) | Claims 8/8 milestones complete |
| Phase 3 roadmap | [../roadmap/PHASE3_AI_AND_SCALABILITY.md](../roadmap/PHASE3_AI_AND_SCALABILITY.md) | Target scope |
| Project status | [PROJECT_STATUS.md](./PROJECT_STATUS.md) | **Stale** — last updated June 7, 2026 |
| ADRs | [../adr/](../adr/) | ADR-001 through ADR-006 |

---

## Executive Verdict

| Question | Answer |
|----------|--------|
| Is Phase 1 complete? | **~70%** — backend foundation strong; exit criteria not met |
| Is Phase 2 complete? | **~40–50%** — milestone scaffolding yes; enterprise guide criteria mostly partial/missing |
| Is the project ready for Phase 3? | **Not yet** — proceed only after Phase 1/2 hardening |

Phase 3 prerequisites in `PHASE3_AI_AND_SCALABILITY.md` require **blob storage operational** and **job queue operational**. Both are **stub/local only** today.

---

# Step 1 — Existing Project Review

## Architecture Snapshot

```
Auditor → Organization (tenant) → Clients → Engagements → Projects / Analysis Runs
                                              ↓
                         Enabled Modules → Upload → Rules → Risk → Findings → Reports
                                              ↓
                         Evidence / Workpapers / Review / Approvals
```

| Layer | Stack | Scale |
|-------|-------|-------|
| Frontend | Next.js 14 App Router, Tailwind, client-side auth gate | 3 duplicated module workspaces + engagement hub |
| Backend | FastAPI 2.0.0, SQLAlchemy, Alembic | **26 routers**, **~34 tables** |
| Database | PostgreSQL, migrations **001–020** | Tenant columns, catalog (22 modules), Phase 2 workflow |
| Deploy | Vercel + Railway | No CI/CD workflows |
| Auth | JWT access + refresh, bcrypt | Org claims in JWT; no MFA/SSO |
| Storage | Local `backend/storage/` | S3 adapter stub only |
| Jobs | FastAPI `BackgroundTasks` | No Redis/Celery/RQ |

## Git History (Recent)

| Commit | Scope |
|--------|-------|
| `650988d` | Phase 1 SaaS + Phase 2 architecture guide |
| `778c29c`–`c8e33ac` | Phase 2 M1–M8 (team, evidence, findings, review, runs, hub) |
| `07edc49` | Fix missing Phase 2 router imports in `main.py` |

Implementation is concentrated on the `architecture` branch. Status documentation lags the codebase.

## Documentation vs Code Gaps

| Document | Claims | Code Reality |
|----------|--------|--------------|
| `PROJECT_STATUS.md` | Phase 1 M3 only, migrations 001–009 | Migrations through **020**, Phase 2 APIs live |
| `PHASE2_FINAL_IMPLEMENTATION_REPORT.md` | 8/8 milestones complete, 86 tests | Milestone **scaffolding** yes; enterprise exit criteria largely unmet |
| `NEXT_STEPS.md` | "Awaiting approval before implementation" | Substantial implementation already done |
| `PHASE1_SAAS_FOUNDATION.md` | All exit criteria unchecked | Many deliverables implemented but not marked complete |

## Completed vs Partial vs Missing (Summary)

### Phase 1

| Item | Status |
|------|--------|
| Migrations 007–013, 020 | ✅ Complete |
| Organizations / members / subscriptions APIs | ✅ Complete |
| Tenant isolation (`organization_id` on clients/engagements) | ✅ Complete (nullable + legacy fallback) |
| Module catalog in PostgreSQL (22 modules) | ✅ Complete |
| Engagement module enable/disable | ✅ Complete |
| JWT `org_id` / `org_role` claims | ✅ Complete |
| `TenantContext` + org-scoped `project_access` | ✅ Complete |
| Subscription enforcement | ⚠️ Partial |
| Audit logging on all mutations | ⚠️ Partial |
| Registration auto-creates org | ❌ Missing |
| Next.js `middleware.ts` on `/dashboard/*` | ❌ Missing |
| Demo account org migration on startup | ❌ Missing |
| Cross-tenant integration tests | ❌ Missing |

### Phase 2

| Item | Status |
|------|--------|
| M1 Engagement team | ✅ Complete |
| M2 Evidence & workpapers | ⚠️ Backend complete; UI partial |
| M3 Finding lifecycle | ⚠️ Backend complete; UI partial |
| M4 Review & approval | ⚠️ Finding-level API only; no run-level review |
| M5 Async analysis runs | ⚠️ Schema + stub job; not wired to rules |
| M6 Storage adapter | ⚠️ Local only; S3 stub |
| M7 Engagement hub | ⚠️ Minimal UI |
| M8 Consolidated report | ⚠️ JSON summary; not Official-run-based |
| Official Run workflow | ❌ Missing (schema column only) |
| Locked run immutability | ❌ Missing |
| Cross-module finding relationships | ❌ Missing |
| Storage lifecycle (archive/retention) | ❌ Missing |
| Auto-workspace on module enable | ❌ Missing |

### Duplicate Functionality & Refactoring Opportunities

| Pattern | Location | Risk |
|---------|----------|------|
| Triplicated backend module stacks | `revenue_*.py`, `procurement_*.py`, journal via `upload`/`analytics` | Blocks modules 4–22 |
| Triplicated frontend workspaces | `JournalEntryTestingWorkspace`, `RevenueTestingWorkspace`, `ProcurementTestingWorkspace` (~280 lines each) | 19 more modules = unmaintainable |
| Dual tenant model | `organization_id` OR `user_id` in `project_access` | Data leakage risk |
| Orphan Next.js register stub | `app/api/auth/register/route.ts` | Misleading dead code |
| Hardcoded subscription in session | `lib/auth/auth.ts` `subscription: "professional"` | Wrong plan display |

---

# Step 2 — Readiness Validation

| Dimension | Ready for Phase 3? | Assessment |
|-----------|-------------------|------------|
| Database design | **Partial** | Solid additive migrations; per-module tables block generic API |
| API structure | **Partial** | 3 parallel module API patterns; no plugin registry |
| Folder structure | **Partial** | No `backend/app/modules/` registry |
| Plugin readiness | **No** | Catalog in DB; no runtime plugin interface |
| Multi-tenancy | **Partial** | `TenantContext` exists; legacy `user_id` fallback active |
| Security | **Partial** | JWT + RBAC; no MFA/SSO, no rate limits, client-side dashboard gate |
| Background jobs | **No** | In-process stub; analysis runs don't invoke rule engine |
| File storage | **No** | Local disk; S3 `NotImplementedError` |
| AI architecture | **No** | No `AIService`, no `ai_recommendations`, credits hardcoded to 0 |
| Scalability | **No** | No Redis, workers, read replicas, load tests, or CI |
| Performance | **Partial** | Pagination on new APIs; no caching; synchronous rule runs |

---

# Step 3 — Detailed Readiness Report

## Existing Architecture

- **Tenant root:** `organizations` with `organization_members` (8 roles, RBAC matrix)
- **Billing:** `subscription_plans` + `organization_subscriptions` (manual plan switch; no Stripe)
- **Catalog:** 22 modules seeded; 3 `built`, 19 `planned`
- **Workflow:** Engagement team, evidence, workpapers, finding lifecycle, review comments, approvals, analysis runs, report history
- **Legacy coexistence:** `audit_projects` + per-module tables (`journal_entries`, `revenue_*`, `procurement_*`)
- **Rule engine:** 21 rules across 3 modules via duplicated service stacks

## Current Project Health

| Dimension | Score | Notes |
|-----------|-------|-------|
| SaaS readiness | **55/100** | Orgs, plans, members exist; enforcement and tests incomplete |
| Enterprise readiness | **45/100** | Workflow APIs exist; Official Run, locking, storage lifecycle missing |
| Module coverage | **14%** | 3 of 22 built |
| Test coverage | **35/100** | ~86 unit tests; no HTTP integration or E2E |
| Documentation accuracy | **30/100** | Status docs lag code |
| Phase 3 readiness | **20/100** | Prerequisites unmet |

## Phase 1 Status (Detailed)

**Estimated completion: ~70%**

| Deliverable | Status | Notes |
|-------------|--------|-------|
| Alembic 007–013, 020 | ✅ | Organizations through audit logs + backfill |
| `/organizations/*`, `/subscriptions/*`, member APIs | ✅ | Invite, roles, plan switch |
| `GET /modules/catalog` | ✅ | 22 modules from DB |
| `/engagements/{id}/modules` | ✅ | Enable/disable with plan checks |
| JWT org claims | ✅ | `org_id`/`org_role` in token; `organization_id`/`member_role` in response |
| `subscription_enforcement.py` | ⚠️ | Wired on client/engagement create, member invite; usage zeros |
| `audit_logs` | ⚠️ | Table exists; manual logging on some routers only |
| Registration → org | ❌ | Org created manually in Settings |
| `middleware.ts` | ❌ | Client-side `DashboardAuthGate` only |
| Integration tests | ❌ | No Firm A vs Firm B HTTP tests |
| Demo org migration | ❌ | `seed_demo_hierarchy` skips org model |

### Phase 1 exit criteria

| Criterion | Met? |
|-----------|------|
| Two auditors same firm see identical client list | ⚠️ Logic exists; no integration test |
| Firm A cannot access Firm B by UUID | ⚠️ Enforced in services; no HTTP test |
| Catalog served from API with 22 modules | ✅ |
| Demo account migrated to org model | ❌ |
| All Phase 1 endpoints write `audit_logs` | ❌ |

## Phase 2 Status (Detailed)

**Estimated completion: ~40–50%** (against `PHASE2_IMPLEMENTATION_GUIDE.md` enterprise criteria)

| Milestone / Criterion | Status |
|-----------------------|--------|
| Engagement team management | ✅ |
| Evidence upload + versioning | ✅ backend / ⚠️ UI |
| Workpaper CRUD | ✅ backend / ⚠️ UI |
| Finding lifecycle + history | ✅ backend / ⚠️ UI |
| Review comments + partner approval | ⚠️ Finding-level only; no frontend |
| Async analysis runs | ⚠️ Stub only; draft→running→completed |
| Engagement hub | ⚠️ Minimal |
| Consolidated report | ⚠️ JSON; not tied to Official Runs |
| Official Run designation | ❌ |
| Locked run immutability | ❌ |
| Run history filters/search | ❌ |
| Cross-module finding relationships | ❌ |
| Storage lifecycle tiers | ❌ |
| Auto-workspace on module enable | ❌ |
| 10k+ row background job | ❌ |
| Blob storage survives redeploy | ❌ (local filesystem) |

## Missing Dependencies (Phase 3 Blockers)

| Dependency | Required By | Current State |
|------------|-------------|---------------|
| Production blob storage (S3/R2) | Evidence, reports, scale | Local filesystem |
| Job queue (Redis + workers) | Async analysis, LLM, reports | `BackgroundTasks` stub |
| `usage_records` + metering | AI credits, Stripe, limits | Not implemented |
| Plugin registry + generic module API | Modules 4–22 | Not implemented |
| Shared `AuditModuleWorkspace` | Frontend scale | 3 duplicated workspaces |
| CI/CD + E2E tests | Safe Phase 3 rollout | No `.github/workflows` |
| Run-level review workflow | LLM human-in-the-loop | Finding-level only |

## Risks

| Risk | Severity | Description |
|------|----------|-------------|
| Phase 3 on unstable Phase 2 | **Critical** | Official Run, locking, async pipeline incomplete |
| Triplicated module architecture | **Critical** | 19 new modules without registry = unmaintainable |
| Dual tenancy model | **High** | `user_id` + `organization_id` coexist |
| Local storage on Railway | **High** | Evidence/reports lost on redeploy |
| Stale documentation | **High** | Wrong assumptions during implementation |
| No integration tests | **High** | Cross-tenant bugs undetected |
| LLM in audit context | **High** | Hallucination liability without approval workflow |

## Technical Debt

| Item | Priority | Phase to Address |
|------|----------|----------------|
| Dual user/org access model | **Critical** | Before Phase 3 |
| 3× backend module stacks | **Critical** | Phase 3 M1 |
| 3× frontend workspaces | **Critical** | Phase 3 M1 |
| Analysis run stub (no real pipeline) | **High** | Phase 2 close-out |
| S3 adapter unimplemented | **High** | Before pilot |
| `usage` hardcoded zeros | **High** | Phase 3 metering |
| `middleware.ts` missing | **High** | Phase 1 close-out |
| Registration doesn't create org | **High** | Phase 1 close-out |
| Consolidated report import bug | **Medium** | Phase 2 bugfix |
| Orphan `app/api/auth/register` stub | **Medium** | Cleanup |
| JWT deprecation warnings in tests | **Low** | Maintenance |

## Security Gaps

| Gap | Priority |
|-----|----------|
| No server-side dashboard route protection | **Critical** |
| Legacy `user_id` tenant bypass path | **Critical** |
| No API rate limiting (plan column unused) | **High** |
| Default JWT secret warning in production | **High** |
| No MFA / SSO backend | **High** |
| Incomplete audit log coverage | **Medium** |
| No login rate limiting | **Medium** |
| Password policy minimal (8 chars) | **Low** |

## Performance Bottlenecks

| Bottleneck | Impact |
|------------|--------|
| Synchronous rule/risk runs in HTTP | Timeouts on large files |
| No caching (engagement hub) | Repeated DB aggregation |
| No read replicas | Dashboard hits primary |
| Full file through API server | Memory pressure |
| Unbounded queries if filters missed | Slow + exposure risk |

## Database Risks

| Risk | Detail |
|------|--------|
| Per-module table sprawl | Each module = 3+ tables without generic model |
| Nullable `organization_id` | Legacy rows may never backfill |
| No partitioning | `audit_findings`, `audit_logs` grow unbounded |
| No archiving strategy | Historical data accumulates |
| Migration numbering confusion in docs | Deployment errors |

## API Risks

| Risk | Detail |
|------|--------|
| 3 incompatible module API prefixes | Breaking change during generic migration |
| No API versioning | Phase 3 may break production frontend |
| Phase 2 endpoints partially wired | UI calls non-functional paths |
| No OpenAPI contract tests | Regression risk |

## Frontend Risks

| Risk | Detail |
|------|--------|
| Client-side auth only | Direct dashboard URL access |
| Triplicated workspaces | 19 modules without shared component |
| Hardcoded subscription in session | Wrong plan display |
| Module catalog hardcoded fallback | Drift from DB |
| No E2E tests | UI regressions undetected |
| Minimal Phase 2 workflow UI | Backend features invisible |

## AI Risks

| Risk | Detail |
|------|--------|
| No AIService or provider abstraction | Vendor lock-in when added |
| No PII redaction before LLM | Compliance violation |
| No confidence scoring or model versioning | Unauditable outputs |
| No human-in-the-loop for narratives | Regulatory liability |
| AI credits not metered | Uncontrolled cost |

## Scalability Risks

| Risk | Detail |
|------|--------|
| Single-process background tasks | Cannot scale horizontally |
| Local file storage | Not multi-instance safe |
| No fair-queue per org | Noisy neighbor |
| No load test harness | 100-firm target unvalidated |
| No Redis | Blocks cache, rate limits, queue |

## Deployment Risks

| Risk | Detail |
|------|--------|
| No CI/CD pipelines | Manual deploy errors |
| Railway ephemeral filesystem | Data loss on redeploy |
| No documented staging environment | Production-only testing |
| No rollback automation | Recovery manual |

## Suggested Refactoring Before Phase 3

| # | Refactor | Priority | Est. Effort |
|---|----------|----------|-------------|
| 1 | Close Phase 1 exit criteria (registration→org, integration tests, demo migration) | **Critical** | 1–2 weeks |
| 2 | Complete Phase 2 enterprise criteria (run lifecycle, Official Run, locking, real async) | **Critical** | 3–4 weeks |
| 3 | Implement production `BlobStorageAdapter` (S3/R2) | **Critical** | 1 week |
| 4 | Introduce Redis + worker framework (Celery or RQ) | **Critical** | 1–2 weeks |
| 5 | Module plugin registry + generic `/modules/{code}/*` router | **Critical** | 2–3 weeks |
| 6 | Shared `AuditModuleWorkspace` frontend component | **High** | 2 weeks |
| 7 | `usage_records` metering | **High** | 1 week |
| 8 | Next.js `middleware.ts` + server auth | **High** | 2–3 days |
| 9 | Remove legacy `user_id` tenant fallback | **High** | 1–2 weeks |
| 10 | Unify storage through adapter | **High** | 3–5 days |
| 11 | CI/CD (lint, pytest, build, E2E) | **High** | 1 week |
| 12 | Sync all status docs to migrations 001–020 | **Medium** | 2–3 days |
| 13 | Feature flag framework | **Medium** | 3–5 days |
| 14 | Fix consolidated report + wire to analysis runs | **Medium** | 3–5 days |

---

# Step 4 — Clarification Questions (Required Before Implementation)

## Business Questions

1. Should AI billing be enabled from Day 1 of Phase 3, or after pilot validation?
2. Will subscription plans differ primarily by AI credits, or also by module access?
3. Are all 22 audit modules mandatory, or a prioritized subset?
4. Should firms be able to disable modules they don't use?
5. Is white-label branding (firm logo, colors, report templates) required in Phase 3?
6. Will external auditors (non-firm users) access the platform?
7. Should in-app/email notifications be configurable per user?
8. What licensing model: per-user, per-firm, per-engagement, or hybrid?
9. Is Stripe the chosen billing provider, or manual invoicing for now?
10. What is the target pilot firm count before public Phase 3 launch?

## Technical Questions

1. Should Redis be mandatory infrastructure from Phase 3 start?
2. Celery, RQ, or ARQ for background workers?
3. Which LLM providers: OpenAI, Azure OpenAI, Anthropic, or multi-provider?
4. Should AI responses be cached (per engagement, per finding)?
5. Should plugin modules be independently deployable, or monorepo-only?
6. Should all reports be generated asynchronously?
7. Deployment target: Railway only, or AWS/GCP/Azure as well?
8. Monitoring stack: Sentry, Datadog, Grafana, or other?
9. Feature flags: env-based, DB-based, or external service?
10. Is OpenAPI v2 (versioned API) required, or incremental deprecation headers?

## Security Questions

1. MFA methods: TOTP only, SMS, hardware keys, or all?
2. SSO: Azure AD only, or Google, Okta, SAML generic?
3. Session timeout policy (access token currently 60 min)?
4. Password policy: complexity, rotation, breach check?
5. Encryption at rest for evidence blobs — required now?
6. Audit log retention period (7 years statutory)?
7. Backup frequency and RPO/RTO targets?
8. Compliance targets: ISO 27001, SOC 2, GDPR — which in scope for Phase 3?
9. Invite tokens: one-time DB tokens vs JWT?
10. Penetration testing before enterprise tier launch?

## Database Questions

1. Schema redesign before generic module tables, or plugin-per-table pattern?
2. Partitioning `audit_findings` / `audit_logs` by org or time — when?
3. Archiving strategy for closed engagements?
4. Data retention: hard delete vs soft delete vs cold storage?
5. Read replica requirement timeline?
6. Is migration 020 applied in production Railway DB?

## AI Questions

1. Confidence score methodology — model output, rule agreement, or hybrid?
2. Explainable AI: must every narrative cite source transactions?
3. Hallucination handling: block export until auditor edits?
4. Prompt versioning and audit trail for prompts?
5. AI model version tracking per recommendation?
6. Human review: mandatory for all LLM output, or only high-risk findings?
7. LLM on finding narratives, executive summaries, or both?
8. PII redaction rules before sending data to LLM?

## Scalability Questions

1. Expected concurrent users (per firm / platform-wide)?
2. Expected firm count at 12 / 36 months?
3. Expected storage growth per firm per year?
4. Target API P95 response times?
5. Availability SLA for Enterprise tier?
6. Disaster recovery: multi-region required?

## DevOps Questions

1. Branching strategy: continue `architecture` → `main`, or release branches?
2. Release cadence: weekly, biweekly, monthly?
3. CI/CD approval process for production deploys?
4. Environments: dev, staging, prod — all required?
5. Rollback strategy: blue-green, previous image, or migration rollback?
6. Infrastructure as Code (Terraform/Pulumi) required?

---

# Step 5 — Phase 3 Feature Impact Analysis

| Feature | Purpose | Business Value | Key Risks | DB Impact | API Impact | Frontend Impact | Effort |
|---------|---------|----------------|-----------|-----------|------------|-----------------|--------|
| Module plugin registry | Add modules without new routers | Scale to 22 modules | Breaking legacy APIs | Low | **High** | **High** | L |
| Generic module API | Unify upload/rules/risk/findings | Faster delivery | Backward compat | Medium | **Critical** | **High** | L |
| Shared AuditModuleWorkspace | One UI for all modules | Reduce 3× debt | Regression in 3 modules | None | Medium | **Critical** | M |
| Redis + workers | Real async analysis | 10k+ row jobs | Ops complexity | Low | Medium | Progress UI | M |
| S3/R2 blob storage | Durable evidence/reports | Production readiness | File migration | Low | Medium | Signed URLs | M |
| `usage_records` metering | Track uploads, storage, AI | Monetization | Accuracy | **New table** | New endpoints | Usage UI | M |
| AIService + LLM | AI-assisted narratives | Differentiation | Hallucination, PII, cost | **`ai_recommendations`** | `/ai/*` | Approval UI | L |
| Stripe webhooks | Automated billing | Self-serve revenue | Webhook security | Medium | `/billing/*` | Checkout | M |
| MFA + SSO | Enterprise auth | Firm adoption | IdP complexity | User columns | Auth changes | Login UX | L |
| Rate limiting | Protect API by plan | Stability | False positives | None | Middleware | None | S |
| Notifications | User alerts | Engagement UX | Delivery infra | **`notifications`** | `/notifications/*` | Center UI | M |
| Executive dashboard | Firm-wide KPIs | Partner visibility | Query perf | Views/cache | New routes | New page | M |
| Modules 4–22 (P1) | Expand catalog | Market coverage | Triplication if no registry | High if old pattern | High if old pattern | High if old pattern | XL |
| CI/CD + E2E | Safe releases | Quality gate | Setup time | None | None | Playwright | M |
| Read replicas | Dashboard scale | Performance | Replication lag | Infra | Read routing | None | M |

**Backward compatibility:** Generic module API is the highest breaking-change risk. ADR-005 recommends gradual migration with deprecation headers.

**Rollback:** Feature flags to route traffic to legacy `/revenue/*`, `/procurement/*`, `/upload` until generic path is proven.

---

# Step 6 — Proposed Implementation Plan (Pending Approval)

## Recommended Order

| Wave | Focus | Duration | Depends On |
|------|-------|----------|------------|
| **0 — Stabilize** | Phase 1 exit + Phase 2 enterprise gaps + doc sync | 4–6 weeks | — |
| **1 — Infrastructure** | S3/R2, Redis, workers, `usage_records`, CI/CD | 3–4 weeks | Wave 0 |
| **2 — Platform** | Plugin registry, generic API, shared workspace, migrate 3 modules | 4–6 weeks | Wave 1 |
| **3 — AI** | AIService, PII redaction, narratives, approval, credit enforcement | 3–4 weeks | Wave 2 |
| **4 — Enterprise** | MFA/SSO, Stripe, rate limits, notifications, executive dashboard | 4–6 weeks | Wave 1 |
| **5 — Modules** | GST Mismatch, Payroll, Bank Reconciliation (P1) | 6–8 weeks | Wave 2 |
| **6 — Scale** | Load tests, read replicas, caching, partitioning plan | 2–4 weeks | Waves 1–5 |

**Total estimate:** 22–34 weeks for full Phase 3 scope (parallel teams can overlap waves).

## Milestone Deliverables

| Milestone | Deliverables | Acceptance Criteria |
|-----------|--------------|---------------------|
| M0 | Phase 1/2 close-out | Integration tests pass; Official Run works; real async job |
| M1 | Infrastructure | Files on S3; jobs on Redis; usage tracked |
| M2 | Generic module platform | Journal works via `/modules/journal_testing/*` |
| M3 | AI narratives | LLM output requires auditor approval before export |
| M4 | Billing + auth | Stripe webhook activates plan; SSO login works |
| M5 | P1 modules | 3 new modules via plugin only |
| M6 | Scale validation | 100-firm load test; E2E in CI green |

## Git Branching Strategy (Proposed)

- `main` — production (Vercel/Railway)
- `architecture` — integration branch (current)
- `phase3/m0-stabilize`, `phase3/m1-infra`, etc. — short-lived feature branches
- No force push to `main`

## Testing Plan (Proposed)

| Layer | Tool | Coverage Target |
|-------|------|-----------------|
| Unit | pytest | Services, RBAC, plugin interface |
| Integration | pytest + TestClient | Cross-tenant isolation, generic module API |
| E2E | Playwright | Login, hub, module upload, invite |
| Load | k6 or Locust | 100 concurrent firms smoke |
| Security | OWASP ZAP (optional) | Auth, IDOR, rate limits |

## Documentation Updates Required

- [PROJECT_STATUS.md](./PROJECT_STATUS.md), [CHANGELOG.md](./CHANGELOG.md), [NEXT_STEPS.md](./NEXT_STEPS.md)
- [02_EXISTING_APIS.md](../api/02_EXISTING_APIS.md) — Phase 2 routers
- New `PHASE3_IMPLEMENTATION_GUIDE.md` (after questions answered)
- Proposed ADR-007: Generic Module Plugin Interface

## Rollback Plan

- Feature flags per module API (`USE_GENERIC_MODULES`)
- Database migrations additive only (ADR-006)
- Blob storage: dual-write period during S3 migration
- Workers: fallback to synchronous for small files if queue unavailable

## Release Plan

1. Wave 0 → internal QA on `architecture`
2. Wave 1 → staging deploy with S3 + Redis
3. Wave 2 → pilot firm on generic journal module
4. Waves 3–5 → phased rollout per module
5. Wave 6 → enterprise tier marketing after load test

---

# Step 7 — Approval Gate

**Phase 3 implementation must not begin until:**

1. Stakeholders answer the clarification questions in Step 4
2. Wave 0 (stabilize Phase 1/2) is explicitly approved
3. Phase 3 scope is agreed (full roadmap vs MVP subset)
4. This report is signed off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Product owner | | | ☐ |
| Tech lead | | | ☐ |
| Security / compliance | | | ☐ |

---

## Summary for Decision-Makers

| Phase | Documentation Claim | Actual State | Ready for Next? |
|-------|---------------------|--------------|-----------------|
| Phase 1 | M3 in progress (June doc) | **~70%** | Needs 2–4 weeks close-out |
| Phase 2 | 8/8 complete (final report) | **~40–50%** vs enterprise guide | Needs 3–5 weeks hardening |
| Phase 3 | Not started | Prerequisites **not met** | **Wait for approval** |

**Recommended immediate action:** Approve **Wave 0 (Stabilize)** before any Phase 3 feature work.

---

## Related Documents

| Document | Path |
|----------|------|
| Phase 3 roadmap | [../roadmap/PHASE3_AI_AND_SCALABILITY.md](../roadmap/PHASE3_AI_AND_SCALABILITY.md) |
| Implementation roadmap | [../roadmap/IMPLEMENTATION_ROADMAP.md](../roadmap/IMPLEMENTATION_ROADMAP.md) |
| Phase 2 enterprise guide | [../roadmap/PHASE2_IMPLEMENTATION_GUIDE.md](../roadmap/PHASE2_IMPLEMENTATION_GUIDE.md) |
| Project status | [PROJECT_STATUS.md](./PROJECT_STATUS.md) |
| Next steps | [NEXT_STEPS.md](./NEXT_STEPS.md) |
| ADR-005 API strategy | [../adr/ADR-005-API-Strategy.md](../adr/ADR-005-API-Strategy.md) |

---

*This report is a living document. Update the review date and approval table when stakeholders respond to Step 4 questions.*
