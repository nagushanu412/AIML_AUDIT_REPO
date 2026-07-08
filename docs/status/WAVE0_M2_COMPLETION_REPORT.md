# Wave 0 — Milestone 2 Completion Report

**Milestone:** Phase 2 Enterprise Workflow Closeout  
**Date:** July 8, 2026  
**Status:** Complete (full E2E UI deferred; core lifecycle APIs + hub UI delivered)

---

## Summary

Milestone 2 closes the highest-priority Phase 2 gaps from [PHASE3_READINESS_REPORT.md](./PHASE3_READINESS_REPORT.md): analysis run lifecycle (submit → approve → lock → designate official → archive), locked-run mutation guards, cross-module finding relationships, auto-workspace on module enable, consolidated report import fix, and engagement hub review/official-run UI.

---

## Files Modified

### Backend

| File | Change |
|------|--------|
| `backend/app/services/analysis_run_service.py` | Lifecycle: submit, approve, return, designate official, archive, mutability guards |
| `backend/app/routers/analysis_runs.py` | REST endpoints for lifecycle actions + audit logs |
| `backend/app/services/run_lock_guard.py` | **New** — blocks mutations on locked/archived runs |
| `backend/app/services/evidence_service.py` | Locked-run guards on upload, version, link |
| `backend/app/services/workpaper_service.py` | Locked-run guards on create, update, upload |
| `backend/app/services/finding_lifecycle_service.py` | Locked-run guards on status/remediation updates |
| `backend/app/services/engagement_module_service.py` | Auto-workspace: project + draft run on module enable |
| `backend/app/services/engagement_hub_service.py` | Fixed missing `save_report_artifact` import |
| `backend/app/services/finding_relationship_service.py` | **New** — cross-module finding links |
| `backend/app/services/module_catalog_constants.py` | `MODULE_CODE_TO_PROJECT_TYPE` reverse map |
| `backend/app/models/audit.py` | `FindingRelationship` model |
| `backend/app/schemas/finding_lifecycle.py` | Relationship request/response schemas |
| `backend/app/routers/finding_lifecycle.py` | `POST/GET/DELETE /findings/{id}/relationships` |

### Database

| File | Change |
|------|--------|
| `backend/alembic/versions/021_finding_relationships.py` | **New** — `finding_relationships` table |

### Frontend

| File | Change |
|------|--------|
| `lib/api/index.ts` | Run lifecycle + finding relationship API helpers |
| `lib/api/types.ts` | `ApiFindingRelationship` type |
| `components/dashboard/EngagementHubClient.tsx` | Official runs panel, lifecycle action buttons, status badges |

### Tests

| File | Change |
|------|--------|
| `backend/tests/test_wave0_m2_phase2.py` | **New** — lifecycle constants, lock guard, relationship types |

---

## API Changes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/engagements/{id}/runs/{run_id}/submit-review` | POST | Completed → under_review |
| `/engagements/{id}/runs/{run_id}/approve` | POST | under_review → locked (partner/manager) |
| `/engagements/{id}/runs/{run_id}/return` | POST | under_review → completed |
| `/engagements/{id}/runs/{run_id}/designate-official` | POST | Partner designates official run (supersedes prior) |
| `/engagements/{id}/runs/{run_id}/archive` | POST | locked/approved → archived |
| `/findings/{id}/relationships` | GET/POST | List/create cross-module finding links |
| `/findings/{id}/relationships/{rel_id}` | DELETE | Remove relationship |

---

## Database Changes

- Migration **021**: `finding_relationships` with engagement/org FK, six relationship types, unique pair constraint

---

## Frontend Changes

- Engagement hub shows **Official Runs** section
- Per-run actions: Submit for review, Approve, Return, Designate official, Archive
- Status badges for lifecycle states

---

## Test Results

| Suite | Result |
|-------|--------|
| `pytest` (full backend) | **103 passed** (pre-M4) |
| `npm run build` | **Success** |

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Background analysis still stub (BackgroundTasks) | Medium | Acceptable for Wave 0; real async is Phase 3 infra |
| Finding relationship UI not in module workspaces | Low | API ready; hub + API tests cover backend |
| Migration 021 must be applied | Medium | Run `alembic upgrade head` before deploy |

---

## Rollback Plan

1. Revert migration 021: `alembic downgrade 020`
2. Revert backend/frontend commits for M2
3. Hub UI falls back to read-only run list (no lifecycle buttons)

---

## Phase 2 Completion After M2

| Criterion | Status |
|-----------|--------|
| Official Run workflow | ✅ API + hub UI |
| Run locking | ✅ Approve → locked; mutation guards |
| Run lifecycle | ✅ Full state machine |
| Run history | ✅ Hub latest_runs + list API |
| Cross-module relationships | ✅ Table + API |
| Auto-workspace | ✅ On module enable |
| Review workflow UI | ⚠️ Hub-level (not per-module workspace) |
| Real async pipeline | ⚠️ Stub (out of Wave 0 scope) |

**Estimated Phase 2 completion:** ~75% (up from ~45%)

---

**Next:** [Wave 0 Milestone 3 — Refactoring](../status/WAVE0_M3_COMPLETION_REPORT.md)
