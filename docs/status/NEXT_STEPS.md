# Next Steps — AIML_AUDIT

**Status:** Documentation complete. **Awaiting approval before implementation.**

---

## Immediate Tasks (This Week)

| # | Task | Owner | Blocker |
|---|------|-------|---------|
| 1 | Review documentation pack with stakeholders | Product / Tech lead | — |
| 2 | Sign off ADRs 001–006 | Tech lead | Doc review |
| 3 | Approve Phase 1 scope and timeline | Product owner | ADR sign-off |
| 4 | Clone production DB to staging for migration rehearsal | DevOps | Railway access |
| 5 | Set strong `JWT_SECRET_KEY` in Railway production | DevOps | None — do now |

### Pre-Implementation Checklist

- [ ] All 31 documentation files reviewed
- [ ] ADRs accepted or amended with comments
- [ ] Phase 1 exit criteria agreed
- [ ] Staging environment available
- [ ] Demo account migration plan approved

---

## Phase 1 — SaaS Foundation (Weeks 1–14)

### Sprint 1–2: Database & Models
- [ ] Alembic 007: `organizations`, `organization_members`
- [ ] Alembic 008: `subscription_plans` (seed Free/Starter/Professional/Enterprise)
- [ ] Alembic 009: `organization_subscriptions`
- [ ] Alembic 010: `audit_module_catalog` (seed 22 modules)
- [ ] Alembic 011: `engagement_enabled_modules`
- [ ] Alembic 012: `audit_logs`
- [ ] Alembic 013: Add `organization_id` to `clients`, `audit_engagements` (nullable)
- [ ] Backfill script: existing users → organizations

### Sprint 3–4: Backend Tenant Isolation
- [ ] `TenantContext` service
- [ ] Update JWT to include `org_id`, `member_role`
- [ ] Refactor `project_access.py` to org-scoped checks
- [ ] `/organizations/*` CRUD + member invite endpoints
- [ ] `/modules/catalog` read from DB
- [ ] `/engagements/{id}/modules` enable/disable
- [ ] Subscription limit middleware (max users, clients)
- [ ] Audit log middleware on mutations
- [ ] Tenant isolation integration tests

### Sprint 5–6: Frontend & Rollout
- [ ] Registration flow creates organization
- [ ] Display firm name in dashboard header
- [ ] Org admin: invite team member UI
- [ ] Next.js middleware protecting `/dashboard/*`
- [ ] Engagement module enablement UI
- [ ] Fetch module catalog from API (replace hardcoded list)
- [ ] Feature flag `USE_ORG_TENANCY`
- [ ] Migrate demo account to org model
- [ ] Update PROJECT_STATUS.md and CHANGELOG.md

**Phase 1 exit criteria:** Two auditors at same firm share clients; Firm A cannot access Firm B data.

---

## Phase 2 — Enterprise Workflow (Weeks 15–26)

### Key Deliverables
- [ ] Engagement hub page (central workspace)
- [ ] `engagement_team_members` table and assignment UI
- [ ] Evidence upload with S3/R2 blob storage
- [ ] Workpapers CRUD
- [ ] Finding lifecycle: Open → In Review → Cleared / Accepted
- [ ] Review comments and partner approval workflow
- [ ] Celery/RQ async jobs for run-rules/risk on large files
- [ ] Consolidated engagement PDF report
- [ ] Deprecate separate workstream navigation panels

**Phase 2 exit criteria:** Auditor attaches evidence to finding; partner approves; async analysis completes for 10k+ rows.

---

## Phase 3 — AI & Scalability (Weeks 27–42+)

### Key Deliverables
- [ ] Module plugin registry
- [ ] Generic `/modules/{code}/*` API
- [ ] Shared `AuditModuleWorkspace` frontend component
- [ ] Build priority modules: GST Mismatch, Payroll, Bank Reconciliation
- [ ] LLM integration with human-in-the-loop approval
- [ ] Usage metering and AI credit enforcement
- [ ] Stripe billing webhooks
- [ ] MFA + Azure AD SSO
- [ ] Executive firm dashboard
- [ ] Load test: 100 concurrent firms
- [ ] CI/CD with E2E test suite

**Phase 3 exit criteria:** New module via catalog + plugin only; 100-firm load test passed; LLM summary with auditor approval.

---

## Long-Term Vision

### Platform Scale
- Support **10,000+ audit firms** on shared infrastructure
- 99.9% uptime SLA for Enterprise tier
- Regional data residency options

### Product Expansion
- **19 remaining modules** from catalog (modules 4–22)
- Client portal for document requests and PBC lists
- Integration connectors: Tally, SAP, Zoho Books, QuickBooks
- Compliance packs: IND AS, IFRS, US GAAP rule templates
- Marketplace for third-party AI audit modules

### AI Capabilities
- Anomaly detection beyond rule-based engine
- Natural language finding narratives (auditor-approved)
- Cross-module correlation (e.g., revenue ↔ GST ↔ bank)
- Predictive risk scoring with explainability

### Business Model
- Self-serve signup with Free tier
- Stripe-powered upgrade flow
- Partner/reseller program for CA networks
- White-label option for large firms

---

## What NOT to Do Yet

Per approved architectural decisions:

- Do **not** rename or drop existing tables
- Do **not** remove `/upload`, `/revenue/*`, `/procurement/*` APIs
- Do **not** build modules 4–22 before Phase 1 tenant foundation
- Do **not** enable LLM before Phase 2 review workflow exists
- Do **not** implement until documentation is approved

---

## References

| Document | Path |
|----------|------|
| Implementation Roadmap | [../roadmap/IMPLEMENTATION_ROADMAP.md](../roadmap/IMPLEMENTATION_ROADMAP.md) |
| Phase 1 Detail | [../roadmap/PHASE1_SAAS_FOUNDATION.md](../roadmap/PHASE1_SAAS_FOUNDATION.md) |
| Project Status | [PROJECT_STATUS.md](./PROJECT_STATUS.md) |
| ADRs | [../adr/](../adr/) |

---

*After approval, start with Alembic migration 007 (`organizations` table).*
