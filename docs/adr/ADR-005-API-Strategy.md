# ADR-005: Gradual Migration to Generic Module APIs

## Status

**Accepted** — June 2026

## Context

Three audit modules are implemented with **duplicated API surface**:

| Module | Prefix |
|--------|--------|
| Journal Entry Testing | `/upload`, `/run-rules`, `/run-risk`, … |
| Revenue Testing | `/revenue/*` |
| Procurement Testing | `/procurement/*` |

Each has identical operations (upload, run-rules, run-risk, risk-scores, generate-findings, findings) with module-specific data tables and rule engines. Adding modules 4–22 with this pattern would create 19 more router files and frontend API clients.

## Decision

**Phase 1–2:** Keep all existing API routes operational. No breaking changes.

**Phase 3:** Introduce generic module API:

```
POST   /modules/{module_code}/upload?project_id=
POST   /modules/{module_code}/run-rules?project_id=
POST   /modules/{module_code}/run-risk?project_id=
GET    /modules/{module_code}/risk-scores?project_id=
POST   /modules/{module_code}/generate-findings?project_id=
GET    /modules/{module_code}/findings?project_id=
```

Legacy routes delegate to the same service layer via a **module plugin registry**. Deprecation headers added to old routes; sunset after 2 release cycles.

Frontend consolidates to one `AuditModuleWorkspace` component parameterized by `module_code`.

## Consequences

### Positive

- New modules require plugin registration, not new routers
- Single API client pattern in frontend
- Existing integrations (if any) continue working during transition
- OpenAPI spec simplified long-term

### Negative

- Temporary duplication: legacy + generic routes coexist
- Plugin interface design must accommodate diverse data schemas (journal vs invoice vs payroll)
- Testing matrix doubles during transition period

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| Big-bang replace all routes | Breaks production; high risk |
| Keep forever separate prefixes | Does not scale to 22 modules |
| GraphQL for modules | Team expertise in REST; over-engineering |
| gRPC internal + REST gateway | Unnecessary complexity for current team size |

## Related Documents

- [../api/01_API_ARCHITECTURE.md](../api/01_API_ARCHITECTURE.md)
- [../api/03_FUTURE_GENERIC_MODULE_API.md](../api/03_FUTURE_GENERIC_MODULE_API.md)
- [../roadmap/PHASE3_AI_AND_SCALABILITY.md](../roadmap/PHASE3_AI_AND_SCALABILITY.md)
