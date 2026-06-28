# 03 — Future Generic Module API

## Purpose

Specify the target unified API pattern for all 22 catalog modules, replacing per-module router duplication.

## Approved Decision

> Gradually migrate toward generic module APIs. Keep existing APIs during transition.

See [../adr/ADR-005-API-Strategy.md](../adr/ADR-005-API-Strategy.md).

## Design Goals

1. One URL pattern for every module
2. Engagement-scoped (not project-type-scoped)
3. Subscription + enablement checks before execution
4. Backward compatible aliases for `/revenue/*`, `/procurement/*`
5. Plugin registry maps `module_code` → service implementation

## Proposed URL Structure

```text
/modules/catalog                          GET    List 22 modules
/modules/catalog/{code}                   GET    Module detail

/engagements/{engagement_id}/modules      GET    Enabled modules for engagement
/engagements/{engagement_id}/modules      POST   Enable module(s)
/engagements/{engagement_id}/modules/{code} DELETE Disable module

/modules/{code}/upload                    POST   ?engagement_id=
/modules/{code}/validate                  POST   Pre-check without persist
/modules/{code}/run-rules                 POST   ?engagement_id=
/modules/{code}/run-risk                  POST   ?engagement_id=
/modules/{code}/risk-scores               GET    ?engagement_id=, pagination
/modules/{code}/findings                  GET    ?engagement_id=
/modules/{code}/findings/generate         POST   ?engagement_id=

/analysis/runs                            POST   Start async pipeline
/analysis/runs/{run_id}                   GET    Status + progress
/analysis/runs/{run_id}/cancel            POST   Cancel job
```

## Module Code Registry (Target)

| Code | Module | Legacy API |
|------|--------|------------|
| `JOURNAL_ENTRY_TESTING` | Journal Entry Testing | `/upload`, `/run-rules`, … |
| `REVENUE_TESTING` | Revenue Testing | `/revenue/*` |
| `PROCUREMENT_TESTING` | Procurement Testing | `/procurement/*` |
| `LEDGER_SCRUTINY` | Ledger Scrutiny | — |
| … | Modules 4–22 | — |

## Request Context (Target)

Every module endpoint requires:

```json
{
  "organization_id": "from JWT",
  "engagement_id": "query or body",
  "module_code": "path param",
  "user_id": "from JWT",
  "member_role": "from JWT"
}
```

**Pre-flight checks:**

1. User belongs to organization
2. Organization subscription active
3. Module entitled by plan
4. Module enabled on engagement
5. User role permitted for action (upload vs approve)

## Plugin Interface (Conceptual)

```python
class ModulePlugin(Protocol):
    code: str
    def validate_upload(self, file_bytes: bytes, engagement: Engagement) -> ValidationResult: ...
    def save_population(self, db, engagement, df) -> int: ...
    def run_rules(self, db, engagement) -> RuleRunResult: ...
    def run_risk(self, db, engagement) -> RiskRunResult: ...
    def generate_findings(self, db, engagement) -> list[Finding]: ...
```

Existing services (`rule_engine`, `revenue_rule_engine`, etc.) implement this behind registry.

## Response Standardization (Target)

```json
{
  "engagement_id": "uuid",
  "module_code": "REVENUE_TESTING",
  "run_id": "uuid",
  "status": "completed",
  "summary": {
    "population_count": 150,
    "violations": 23,
    "high_risk": 5,
    "medium_risk": 10,
    "low_risk": 8
  }
}
```

## Deprecation Plan

| Phase | Action |
|-------|--------|
| Phase 3a | Ship generic API; legacy routes call same services |
| Phase 3b | OpenAPI marks legacy as deprecated |
| Phase 3c | Frontend switches to generic client |
| Phase 4 | Remove legacy routes (major version bump) |

## Advantages

- Adding module 4 = register plugin, not new router file
- Consistent frontend SDK
- Easier API documentation for integrators

## Disadvantages

- Abstraction layer complexity
- Module-specific validation harder to express in OpenAPI generics
- Migration period with duplicate routes

## Risks

| Risk | Mitigation |
|------|------------|
| Lowest-common-denominator API | Module-specific extensions in metadata |
| Breaking existing frontend | Aliases until migration complete |

## Recommendations

1. Implement registry with 3 existing modules first
2. Do not build module 4 until registry exists
3. Version API as `/v2/` when generic routes ship

---

*Related: [../business/03_MODULE_CATALOG.md](../business/03_MODULE_CATALOG.md)*
