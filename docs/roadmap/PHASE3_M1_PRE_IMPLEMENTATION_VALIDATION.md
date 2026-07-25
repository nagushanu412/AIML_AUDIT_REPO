# Phase 3 Milestone 1 — Pre-Implementation Architecture Validation

**Document type:** Architecture validation (no code)  
**Date:** July 8, 2026  
**Scope:** Validate three concerns before Phase 3 M1 (Generic Module Framework)  
**Prerequisites stated:** Phase 1, Phase 2, Wave 0 complete; Phase 3 architecture approved

**Related:**

- [PHASE3_TECHNICAL_DESIGN_AND_EXECUTION_PLAN.md](./PHASE3_TECHNICAL_DESIGN_AND_EXECUTION_PLAN.md)
- [ADR-005-API-Strategy.md](../adr/ADR-005-API-Strategy.md)

---

# Executive Summary

| Item | Verdict | M1 Impact |
|------|---------|-----------|
| Analysis Run Worker | **Lifecycle service complete; pipeline worker is a stub** | M1 must add real orchestration without replacing Rule Engine |
| Organization vs User | **Dual-field model correct; org-first access fallback exists** | Do **not** remove `user_id`; defer fallback removal from M1 critical path |
| API Versioning | **`/api/v2/` not required** for this project | Use `/modules/{code}/*` per ADR-005; skip version prefix |

**Final decision:** Phase 3 M1 should **proceed with two plan amendments** (no `/api/v2/`, real Analysis Engine orchestration). Architecture is otherwise ready.

---

# Item 1 — Analysis Run Worker Review

## Current Status

The Phase 2 Analysis Run implementation has **two separate layers** with very different maturity:

### Layer A — `AnalysisRunService` (complete lifecycle state machine)

**File:** `backend/app/services/analysis_run_service.py`

| Capability | Status |
|------------|--------|
| Create draft run | ✅ |
| Start run (draft → running) | ✅ |
| Complete / fail run | ✅ |
| Submit for review | ✅ |
| Approve → locked | ✅ |
| Return to auditor | ✅ |
| Designate official run | ✅ |
| Archive | ✅ |
| Concurrent run guard | ✅ |
| Immutability guard (`locked`, `archived`) | ✅ |

This is **not a placeholder**. It is a full **workflow / governance engine** for analysis runs.

### Layer B — `_process_run_background` (placeholder worker)

**File:** `backend/app/routers/analysis_runs.py` (lines 59–82)

```python
def _process_run_background(run_id: UUID) -> None:
    # Sets progress 50% → "Running rules and risk scoring"
    # Sets progress 100% → status "completed"
    # Does NOT call upload, validation, rules, risk, or findings
```

**Classification:** **Placeholder stub** — simulates progress only.

Uses FastAPI `BackgroundTasks` (in-process, not Redis/worker queue).

### Layer C — Module workspaces (actual audit pipeline today)

**Files:** `JournalEntryTestingWorkspace.tsx`, `RevenueTestingWorkspace.tsx`, `ProcurementTestingWorkspace.tsx`

The **real** audit pipeline runs **outside** analysis runs, via direct HTTP calls:

```
uploadJournalFile / uploadRevenueFile / uploadProcurementFile  (includes validation)
    → runRules
    → runRisk
    → generateFindings
    → fetchRiskScores + fetchFindings
```

Reports are generated separately via `generateReport()` in export sections.

**Analysis runs are not invoked** from module workspaces today.

### Layer D — Partial integration elsewhere

| Integration | Status |
|-------------|--------|
| Auto-create draft run on module enable | ✅ `engagement_module_service._ensure_module_workspace` |
| `analysis_run_id` on evidence/workpapers | ✅ Schema exists |
| `run_lock_guard` on evidence, workpapers, findings lifecycle | ✅ Wired |
| `run_lock_guard` on upload / run-rules endpoints | ❌ Not wired |
| Engagement Hub lists runs | ✅ Display only |
| Frontend `startAnalysisRun` API client | ✅ Exists in `lib/api/index.ts` but workspaces don't use it |

---

## Issues

| # | Issue | Severity |
|---|-------|----------|
| 1 | Background worker does not execute audit pipeline | **Critical** |
| 2 | Two parallel execution paths (workspace direct vs analysis run) | **High** |
| 3 | Upload/rules not protected by run lock guard | **Medium** |
| 4 | `BackgroundTasks` won't scale to large files or multi-instance deploy | **High** (M1 infra) |
| 5 | Progress messages claim "Running rules" but nothing runs | **Medium** (misleading UX) |
| 6 | Official run / locked state disconnected from actual findings data | **High** |

---

## Proposed Execution Order (Validation)

The approved pipeline order is **correct** for Phase 3:

```
Upload
  ↓
Validation
  ↓
Rule Engine          ← PRIMARY audit engine (unchanged)
  ↓
Risk Engine
  ↓
Findings Engine
  ↓
AI Narrative         ← OPTIONAL (Phase 3 M4; advisory only)
  ↓
Report Generation
  ↓
Run Completion
```

### Confirmations

| Statement | Correct? |
|-----------|----------|
| Rule Engine remains primary audit engine | ✅ **Yes** |
| AI must NOT replace rules | ✅ **Yes** — AI is post-findings, human-approved narrative only |
| Analysis Run Worker should orchestrate this sequence | ✅ **Yes** — it is the orchestrator, not the rule evaluator |
| Upload can happen before run start (user uploads file, then starts run) | ✅ **Yes** — upload may precede `POST .../runs/{id}/start`; run executes steps 2–7 on existing project data |

### Clarification

The Analysis Engine **calls** existing rule/risk/findings services. It does **not** replace them. Think:

- **Rule Engine** = worker that applies audit logic
- **Analysis Engine** = conductor that calls workers in order and updates run progress

---

## Recommendations for Phase 3 M1

| # | Recommendation | Milestone |
|---|----------------|-----------|
| 1 | Introduce `AnalysisEngine.execute_run(run_id)` that calls generic Upload (if needed) → Validation → RuleEngine → RiskEngine → FindingsEngine → ReportEngine | **M1** |
| 2 | Replace `_process_run_background` stub with `AnalysisEngine` invocation | **M1** |
| 3 | Keep `AnalysisRunService` lifecycle methods unchanged (governance layer) | **M1** |
| 4 | Update progress_pct per step (10/30/50/70/90/100) | **M1** |
| 5 | Wire module workspaces to optionally use run-based flow (feature flag) | **M2** |
| 6 | Apply `run_lock_guard` to upload and run-rules when project linked to locked run | **M1** |
| 7 | Move worker from `BackgroundTasks` to Redis queue when Wave 0 Redis is available | **M1/M9** |
| 8 | AI narrative step is **no-op stub** in M1; real implementation in M4 | **M4** |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Breaking current workspace direct-call flow | Keep both paths during M1; converge in M2 |
| Long-running analysis blocks API | Worker queue with status polling |
| Run completes without data uploaded | Pre-flight check: project must have records before rules step |

---

## Final Decision — Analysis Run Worker

| Question | Answer |
|----------|--------|
| Is it a placeholder? | **Partially** — lifecycle is real; pipeline worker is stub |
| Is it sequential execution? | **No** — pipeline not connected |
| Is it complete orchestration? | **No** |
| Is proposed pipeline order correct? | **Yes** |
| Should Rule Engine be replaced? | **No** |

**Decision:** M1 must implement **real orchestration** in `AnalysisEngine` while preserving `AnalysisRunService` governance and all existing rule engines.

---

# Item 2 — Organization Model Review

## Current Status

### Intended model (validated)

| Field | Purpose | Correct? |
|-------|---------|----------|
| `organization_id` | Tenant isolation, data ownership, client/engagement ownership | ✅ |
| `user_id` | Login, auth, audit trail, created_by, assignments, reviewer identity | ✅ |

Both fields are stored on `clients` at creation:

```python
Client(user_id=tenant.user.id, organization_id=tenant.organization_id, ...)
```

**This dual-storage model is correct.** `user_id` should **not** be removed.

### Access control model (today)

**File:** `backend/app/services/project_access.py`

```python
def _client_accessible(client, tenant):
    if tenant.organization_id:
        return client.organization_id == tenant.organization_id   # ORG ONLY
    return client.user_id == tenant.user.id                       # USER FALLBACK

def client_list_filter(tenant):
    if tenant.organization_id:
        return Client.organization_id == tenant.organization_id  # ORG ONLY
    return Client.user_id == tenant.user.id                     # USER FALLBACK
```

**Behavior:**

- User **with** organization → access by `organization_id` **only** (ignores `user_id` match)
- User **without** organization → access by `user_id` **only** (legacy solo auditor)

This is **either/or**, not both combined with OR.

---

## Legacy Logic Found

### Primary tenant fallback (data access)

| Location | Logic | Why it exists |
|----------|-------|---------------|
| `project_access.py` → `_client_accessible()` | If no `tenant.organization_id`, use `user_id` | Legacy solo auditors before org model |
| `project_access.py` → `client_list_filter()` | Same pattern for list queries | Same |
| `project_access.py` → `ensure_engagement_organization_id()` | Falls back to `tenant.organization_id` when engagement/client org null | Backfill legacy engagements |

### Subscription / plan gating (soft skip)

| Location | Logic | Why it exists |
|----------|-------|---------------|
| `subscription_enforcement.py` | `if not tenant.organization_id: return` (skip limit checks) | Solo users bypass plan enforcement |
| `engagement_module_service.py` → `_assert_plan_allows_module()` | Same — skip if no org | Same |

### Auth / org resolution

| Location | Logic | Why it exists |
|----------|-------|---------------|
| `tenant_context.py` → `validate_token_org_claims()` | Error if token has org but user has none | JWT/org mismatch guard |
| `tenant_context.py` → `resolve_for_user()` | Resolve org from `default_organization_id` or first active membership | Org context bootstrap |

### Operational / non-access

| Location | Logic | Why it exists |
|----------|-------|---------------|
| `audit_logs.py` | Requires `tenant.organization_id` for log listing | Org-scoped audit trail |
| `seed_service.py` | Demo seed uses `Client.user_id == user.id` | Demo data bootstrap |
| `scripts/backfill_tenant_data.py` | Uses `client.user_id` to find owner for backfill | One-time migration script |

### Tests documenting fallback

| Location | Logic |
|----------|-------|
| `tests/test_wave0_m1_phase1.py` | `test_client_list_filter_user_fallback_without_org` |
| `tests/test_wave0_m1_phase1.py` | `test_client_list_filter_org_only_when_tenant_has_org` |

---

## Is the proposed architecture correct?

| Statement | Verdict |
|-----------|---------|
| `organization_id` for tenant isolation & ownership | ✅ **Correct** |
| `user_id` for auth, audit, assignments (not tenant boundary) | ✅ **Correct** |
| Keep both fields in the system | ✅ **Correct** |
| Current either/or access fallback | ⚠️ **Transitional** — correct for migration, not long-term |

### Gap vs target architecture

The fallback (`if no org → use user_id for data access`) **conflates** `user_id` into a tenant boundary role. Long-term:

- **Every production user should have an organization** (even solo CA = single-user org)
- `user_id` remains on records for **provenance** (`created_by`, `assigned_by`, `run_owner_id`)
- **Access queries should always filter by `organization_id`**

The fallback should eventually be removed, but **`user_id` columns stay**.

---

## Recommendations

| # | Recommendation | When |
|---|----------------|------|
| 1 | **Do NOT remove `user_id`** from clients, engagements, audit logs, team assignments | Never |
| 2 | **Do NOT remove org-first access logic** — it is correct for org users | Now |
| 3 | **Defer fallback removal** from M1 critical path | M1 prep task or pre-M2 |
| 4 | Require organization on registration (Wave 0 — stated complete) | Verify |
| 5 | Backfill `organization_id` on all legacy clients (migration 020 pattern) | Before fallback removal |
| 6 | Add integration test: org user cannot see other org's client even if `user_id` matches | M1 testing |
| 7 | Change subscription enforcement to **require** org (no silent skip) once all users have orgs | Pre-M2 |
| 8 | Document in ADR: `user_id` = actor; `organization_id` = tenant boundary | M1 week 1 |

### Should fallback be removed during Milestone 1?

**No — not as part of M1 Generic Module Framework deliverables.**

| Reason | Detail |
|--------|--------|
| Scope separation | M1 is plugin framework, not tenant migration |
| Risk | Removing fallback before 100% org backfill breaks solo/legacy accounts |
| Timing | Remove in dedicated **Tenant Hardening** task before M2 migration |

M1 should **design generic engines to accept `TenantContext` with `organization_id`** and not introduce new `user_id` access paths.

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Legacy client with null `organization_id` invisible to org users | Medium | Migration 020 + backfill script |
| Fallback masks missing org on new records | Medium | Require org on client create (already sets both fields) |
| Confusion between actor `user_id` and tenant `organization_id` | Low | ADR documentation |

---

## Final Decision — Organization Model

| Question | Answer |
|----------|--------|
| Is dual-field architecture correct? | **Yes** |
| Should `user_id` be removed? | **No** |
| Should fallback be removed in M1? | **No** — defer to tenant hardening |
| Is org-first access correct for org users? | **Yes** |

**Decision:** Architecture is **correct**. M1 proceeds without fallback removal. Add tenant hardening as a parallel or pre-M2 gate.

---

# Item 3 — API Review

## Current Status

### API surface today

| Group | Pattern | Count |
|-------|---------|-------|
| Journal module | Root paths: `/upload`, `/run-rules`, `/run-risk`, `/generate-findings`, `/findings`, `/reports` | 6+ endpoints |
| Revenue module | `/revenue/*` | 6 endpoints |
| Procurement module | `/procurement/*` | 6 endpoints |
| Phase 2 platform | `/engagements/{id}/team|evidence|workpapers|findings|runs|hub` | 30+ endpoints |
| SaaS | `/organizations`, `/subscriptions`, `/modules/catalog` | 15+ endpoints |
| Auth | `/auth/*` | 6 endpoints |

**Total:** ~26 routers in `main.py`

### Project constraints (stated)

| Constraint | Value |
|------------|-------|
| Backend + frontend developed together | Yes |
| Public APIs | No |
| Mobile app | No |
| External consumers | No |
| Third-party integrations | No |

### Existing ADR position

**ADR-005** specifies generic routes as:

```
/modules/{module_code}/upload
/modules/{module_code}/run-rules
...
```

**Not** `/api/v2/modules/...`

The Phase 3 Technical Design document introduced `/api/v2/` which **conflicts with ADR-005** and adds unnecessary prefix for a monolithic app.

---

## Need for `/api/v2/` Versioning?

### Analysis

| Argument for `/api/v2/` | Applies here? |
|-------------------------|---------------|
| External consumers need stable contract | ❌ No external consumers |
| Mobile app on different release cycle | ❌ No mobile |
| Breaking changes without frontend deploy | ❌ Monorepo — deploy together |
| Public API marketplace | ❌ Not planned |
| Multiple frontend versions in production | ❌ Single Next.js app |

**Conclusion:** URL path versioning (`/api/v2/`) provides **minimal value** for this project today.

### When versioning would matter (future)

- Public API for third-party integrations
- Mobile app
- Partner ERP connectors (Tally, SAP)
- Big Four API automation

None of these are in M1 scope.

---

## Alternative Recommendations (preferred over `/api/v2/`)

| # | Approach | Value |
|---|----------|-------|
| 1 | **Standardize on `/modules/{code}/*`** per ADR-005 | High — one pattern for 22 modules |
| 2 | **Keep legacy routes as thin shims** during M2 migration | High — zero frontend breakage |
| 3 | **Unified response envelopes** — `{ data, meta, errors }` or consistent list `{ items, total, limit, offset }` | Medium |
| 4 | **Standardized error schema** — `{ detail, code, field }` across all routers | Medium |
| 5 | **OpenAPI 3.1** auto-generated at `/docs` + exported `openapi.json` in CI | High |
| 6 | **Deprecation headers** on legacy routes: `Deprecation: true`, `Sunset: <date>` | Medium |
| 7 | **Internal API changelog** in `docs/api/CHANGELOG.md` | Medium |
| 8 | **Consistent query params** — `project_id`, `engagement_id`, `limit`, `offset` naming | Medium |

### Proposed generic routes (M1 — no version prefix)

```
GET    /modules/catalog
GET    /modules/{code}/metadata
POST   /modules/{code}/upload?project_id=
POST   /modules/{code}/run-rules?project_id=
POST   /modules/{code}/run-risk?project_id=
GET    /modules/{code}/risk-scores?project_id=
POST   /modules/{code}/generate-findings?project_id=
GET    /modules/{code}/findings?project_id=
POST   /modules/{code}/reports/generate?project_id=
GET    /modules/{code}/reports?project_id=
```

Frontend `lib/api/index.ts` adds `moduleApi.*` functions; legacy functions remain until M2.

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking frontend during route migration | High | Shims + monorepo deploy |
| Inconsistent error shapes across modules | Medium | Shared `handle_service_error` + schema |
| Future need for public API | Low | Introduce `/api/v1/` when first external consumer appears — not before |
| ADR-005 vs Phase 3 doc conflict | Medium | Amend Phase 3 doc to remove `/api/v2/` |

---

## Final Decision — API Versioning

| Question | Answer |
|----------|--------|
| Is `/api/v2/` necessary in Phase 3? | **No** |
| What instead? | `/modules/{code}/*` + consistency improvements |
| Keep legacy routes? | **Yes** — shims through M2 |
| Update ADR-005? | **No** — ADR-005 is already correct |

**Decision:** **Do not introduce `/api/v2/`.** Standardize naming and responses; follow ADR-005.

---

# Final Recommendation

## Question 1 — Should Phase 3 Milestone 1 proceed exactly as currently planned?

### Answer: **YES, with two amendments**

| Amendment | Change |
|-----------|--------|
| **A** | Remove `/api/v2/` prefix from M1 plan; use `/modules/{code}/*` per ADR-005 |
| **B** | M1 deliverable explicitly includes **real `AnalysisEngine` orchestration** replacing the `_process_run_background` stub (Rule Engine unchanged) |

All other M1 scope (plugin registry, generic engines, `module_plugin_config`, `AuditModuleWorkspace` shell) remains as planned.

| Item | Proceed as planned? |
|------|---------------------|
| Generic Module Framework | ✅ Yes |
| ModuleProvider protocol | ✅ Yes |
| Generic engines (upload/validate/rules/risk/findings/reports) | ✅ Yes |
| `/api/v2/` prefix | ❌ No — use `/modules/{code}/*` |
| AnalysisEngine wiring | ✅ Yes — elevate from stub to explicit M1 deliverable |
| Remove user_id fallback | ❌ No — defer to tenant hardening |
| Remove user_id from system | ❌ No — keep for auth/audit/assignments |

---

## Question 2 — Should any changes be made to the approved Phase 3 Architecture before implementation?

### Answer: **Yes — three documentation amendments, no structural redesign**

| # | Amendment | Type |
|---|-----------|------|
| 1 | **API paths:** Replace all `/api/v2/modules/{code}/*` references with `/modules/{code}/*` | Doc update |
| 2 | **Analysis Engine:** Explicitly document as orchestrator calling Rule Engine (not replacement); include pipeline step diagram in M1 acceptance criteria | Doc update |
| 3 | **Tenant model:** Add ADR note — `organization_id` = tenant boundary; `user_id` = actor/provenance; fallback removal is pre-M2 hardening, not M1 | Doc update |

### No change required to:

- Plugin architecture
- Generic engines concept
- Migrate-3-then-build-19 strategy (M2 then M3)
- UI unchanged principle
- Rule Engine as primary audit engine
- Dual `organization_id` + `user_id` storage

---

## Architecture Readiness Verdict

| Dimension | Ready? |
|-----------|--------|
| Generic Module Framework design | ✅ Yes |
| Analysis run orchestration plan | ✅ Yes (with M1 amendment) |
| Organization model | ✅ Yes |
| API strategy | ✅ Yes (without `/api/v2/`) |
| Phase 1/2/Wave 0 compatibility | ✅ Yes — GMMF extends existing services |

### Pre-M1 checklist (non-blocking but recommended)

- [ ] Update `PHASE3_TECHNICAL_DESIGN_AND_EXECUTION_PLAN.md` — remove `/api/v2/`
- [ ] Draft ADR-007: ModuleProvider Protocol
- [ ] Draft ADR-008: Tenant Boundary (`organization_id` vs `user_id` roles)
- [ ] Add M1 acceptance test: AnalysisEngine executes full pipeline on fixture data
- [ ] Confirm Redis/worker available from Wave 0 for background execution

---

## Summary Table

| Item | Current Status | Final Decision |
|------|----------------|----------------|
| **Analysis Run Worker** | Lifecycle ✅ / Pipeline stub ❌ | M1: real AnalysisEngine; Rule Engine unchanged |
| **Organization Model** | Dual-field ✅ / Fallback transitional ⚠️ | Keep both IDs; defer fallback removal |
| **API Versioning** | 3 incompatible prefixes today | No `/api/v2/`; use `/modules/{code}/*` |

**Phase 3 Milestone 1 is approved to begin** after the three documentation amendments above.

---

*Validation complete. No code changes required for this document.*
