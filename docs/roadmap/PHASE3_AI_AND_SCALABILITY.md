# Phase 3 — AI & Scalability

## Purpose

Scale platform to 100–10,000+ firms, implement generic module architecture, add real AI/LLM capabilities, and build remaining catalog modules.

## Duration (Estimate)

12–16 weeks (ongoing module development beyond)

## Prerequisites

- Phase 2 complete
- Blob storage and job queue operational

## Goals

1. Generic `/modules/{code}/*` API with plugin registry
2. Build catalog modules 4–22 (prioritized roadmap)
3. LLM integration for narratives and executive summaries
4. Usage metering and AI credit enforcement
5. MFA + SSO (Azure AD)
6. Executive firm dashboard
7. Performance: caching, read replicas, horizontal workers
8. Full test suite + CI/CD

## Database Deliverables

| Table | Purpose |
|-------|---------|
| `usage_records` | Meter uploads, storage, AI credits |
| `ai_recommendations` | Store LLM outputs + confidence |
| `report_templates` | Firm-branded layouts |
| `notifications` | User alerts |
| `materiality_settings` | Per engagement |
| `audit_samples` | Sampling records |

## Backend Deliverables

| Item | Description |
|------|-------------|
| Module plugin registry | Register 22 modules |
| Generic module router | `/modules/{code}/*` |
| Deprecate legacy prefixes | Sunset plan |
| AIService | OpenAI/Azure with PII redaction |
| Stripe webhooks | Automated billing |
| Rate limiting | Per org API limits |
| Read replica support | Dashboard queries |
| OpenAPI v2 | Versioned API |

## Frontend Deliverables

| Item | Description |
|------|-------------|
| Shared AuditModuleWorkspace | Replace 3 duplicated workspaces |
| AI narrative UI | Human approve before export |
| Executive dashboard | Cross-engagement KPIs |
| Notification center | In-app alerts |
| Module builder admin | Enable beta modules |

## Module Build Priority (Suggested)

| Priority | Modules |
|----------|---------|
| P1 | GST Mismatch, Payroll, Bank Reconciliation |
| P2 | Ledger Scrutiny, Duplicate Payment, Invoice Checking |
| P3 | Fixed Asset, TDS, IT Controls modules |
| P4 | Remaining catalog modules |

## Exit Criteria

- [ ] New module added via catalog row + plugin (no new router file)
- [ ] 100 concurrent firms load test passed
- [ ] LLM summary on engagement with auditor approval
- [ ] Stripe subscription lifecycle works
- [ ] E2E test suite in CI

## Long-Term Vision

- 10,000+ audit firms on shared infrastructure
- Marketplace for custom AI modules
- Client portal for document requests
- Integration with Tally, SAP, Zoho exports
- Regional compliance packs (IND AS, IFRS, US GAAP)

## Risks

| Risk | Mitigation |
|------|------------|
| LLM hallucination in audit context | Human-in-the-loop; rules remain source of truth |
| Module sprawl | Strict plugin interface reviews |
| Phase 1/2 gaps block Phase 3 | Complete [Phase 3 Readiness Report](../status/PHASE3_READINESS_REPORT.md) Wave 0 first |

## Recommendations

- Do not enable LLM on findings until Phase 2 review workflow exists
- Performance test at 1,000 firms before marketing enterprise tier
- **Read [PHASE3_READINESS_REPORT.md](../status/PHASE3_READINESS_REPORT.md) before starting implementation**

---

*Related: [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)*
