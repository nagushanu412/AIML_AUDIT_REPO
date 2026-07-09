# Phase 3 Implementation Guide

**Status:** Milestones 1–2 complete  
**Branch:** `feature/phase3-m2-module-migration`  
**Last updated:** July 9, 2026

---

## Overview

Phase 3 transforms AIML_AUDIT into a scalable, plugin-based enterprise AI audit platform. Implementation follows the approved technical design with these **final decisions**:

| Decision | Implementation |
|----------|----------------|
| Generic Module Framework | `backend/app/services/module_framework/` |
| API routing | `/modules/{moduleCode}/*` per ADR-005 (no `/api/v2/`) |
| Rule Engine | Unchanged — primary audit engine |
| AI | `LLMProvider` interface only (M4) |
| Multi-tenant | `organization_id` + `user_id` both retained |
| Module migration | M2 — not M1 |

---

## Milestone 1 — Generic Module Framework (Complete)

### Objectives

- Plugin architecture and module registry
- Generic engines (upload, validation, rules, risk, findings, report, analysis)
- Generic REST API at `/modules/{code}/*`
- AnalysisEngine orchestration replacing background stub
- `AuditModuleWorkspace` shell (not wired to existing routes)
- Database: `module_plugin_config`, `feature_flags`, catalog extensions

### What Was NOT Done (By Design)

- Journal / Revenue / Procurement UI migration
- Legacy route removal
- AI narrative implementation
- Billing, notifications, dashboards, scalability

---

## Architecture

```
/modules/{code}/*          Generic REST router
        ↓
ModuleRegistry           Resolves plugin by code
        ↓
ModuleProvider           Journal / Revenue / Procurement plugins
        ↓
Generic Engines          Upload → Validate → Rules → Risk → Findings → Report
        ↓
Existing Services        rule_runner, risk_scoring, findings_service, etc.
```

### Analysis Pipeline (AnalysisEngine)

```
Validation (data exists)
  → Rule Engine
  → Risk Engine
  → Findings
  → AI Narrative (no-op, M4)
  → Report
  → Run Completion
```

Triggered by `POST /engagements/{id}/runs/{run_id}/start` via `BackgroundTasks`.

---

## Key Paths

| Area | Path |
|------|------|
| Protocol | `backend/app/services/module_framework/protocol.py` |
| Registry | `backend/app/services/module_framework/registry.py` |
| Engines | `backend/app/services/module_framework/engines.py` |
| Plugins | `backend/app/services/module_framework/plugins/` |
| LLM abstraction | `backend/app/services/module_framework/llm_provider.py` |
| Generic API | `backend/app/routers/generic_modules.py` |
| Workspace shell | `components/modules/AuditModuleWorkspace.tsx` |
| Legacy adapter | `backend/app/services/module_framework/legacy_adapter.py` |

---

## Generic API Endpoints

| Method | Path |
|--------|------|
| GET | `/modules/{code}/metadata` |
| GET | `/modules/{code}/workspace-config` |
| POST | `/modules/{code}/upload?project_id=` |
| POST | `/modules/{code}/run-rules?project_id=` |
| POST | `/modules/{code}/run-risk?project_id=` |
| GET | `/modules/{code}/risk-scores?project_id=` |
| POST | `/modules/{code}/generate-findings?project_id=` |
| GET | `/modules/{code}/findings?project_id=` |
| GET | `/modules/{code}/reports?project_id=` |
| POST | `/modules/{code}/reports/generate?project_id=` |
| GET | `/modules/{code}/reports/{id}/download` |

Legacy routes (`/upload`, `/revenue/*`, `/procurement/*`) remain unchanged.

---

## Milestone 2 — Existing Module Migration (Complete)

### Delivered

- Legacy routers are thin shims via `LegacyModuleAdapter`
- All three modules execute through generic engines + plugins
- `AuditModuleWorkspace` wraps existing module pages (no visual change)
- Generic API client available at `lib/api/modules.ts`
- Parity validated on sample xlsx fixtures

### Legacy Shim Map

| Legacy | Module Code | Generic Engine |
|--------|-------------|----------------|
| `/upload` | `JOURNAL_ENTRY_TESTING` | UploadEngine |
| `/run-rules` | `JOURNAL_ENTRY_TESTING` | RuleEngineService |
| `/run-risk`, `/findings`, `/reports` | `JOURNAL_ENTRY_TESTING` | Risk/Findings/Report engines |
| `/revenue/*` | `REVENUE_TESTING` | All engines |
| `/procurement/*` | `PROCUREMENT_TESTING` | All engines |

---

## Milestone 3 — Next Steps (Pending Approval)

1. Register P1 modules (GST Mismatch, Bank Reconciliation, Payroll) via plugin config only
2. No new routers — use `/modules/{code}/*` exclusively
3. Per-module acceptance template (5 rules, 1 report)

**Do not start M3 without explicit approval.**

---

## Testing

```bash
cd backend && pytest tests/ -q
cd .. && npm run build
```

Phase 3 tests:

- `backend/tests/test_phase3_m1_framework.py`
- `backend/tests/test_phase3_m1_api.py`
- `backend/tests/test_phase3_m2_parity.py`

---

## Related Documents

- [PHASE3_TECHNICAL_DESIGN_AND_EXECUTION_PLAN.md](./PHASE3_TECHNICAL_DESIGN_AND_EXECUTION_PLAN.md)
- [PHASE3_M1_PRE_IMPLEMENTATION_VALIDATION.md](./PHASE3_M1_PRE_IMPLEMENTATION_VALIDATION.md)
- [PHASE3_M1_COMPLETION_REPORT.md](../status/PHASE3_M1_COMPLETION_REPORT.md)
- [ADR-005-API-Strategy.md](../adr/ADR-005-API-Strategy.md)
