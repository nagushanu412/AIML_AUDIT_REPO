# AIML_AUDIT Documentation Index

Enterprise SaaS documentation and architecture blueprint for the AIML Audit Analytics Platform.

**Documentation-only.** No source code in this folder modifies application behavior.

## Quick Links

| Area | Path |
|------|------|
| Architecture Review (full gap analysis) | [ENTERPRISE_SAAS_ARCHITECTURE_REVIEW.md](./ENTERPRISE_SAAS_ARCHITECTURE_REVIEW.md) |
| Project Status | [status/PROJECT_STATUS.md](./status/PROJECT_STATUS.md) |
| Implementation Roadmap | [roadmap/IMPLEMENTATION_ROADMAP.md](./roadmap/IMPLEMENTATION_ROADMAP.md) |
| Next Steps | [status/NEXT_STEPS.md](./status/NEXT_STEPS.md) |

## Folder Structure

```
docs/
├── README.md                          ← You are here
├── ENTERPRISE_SAAS_ARCHITECTURE_REVIEW.md
├── architecture/                      System & SaaS architecture
├── database/                          Schema, ER, migrations
├── api/                               API design & endpoints
├── business/                          Subscription, org, modules, engagements
├── roadmap/                           Phased implementation plans
├── adr/                               Architecture Decision Records
└── status/                            Status, changelog, next steps
```

## Approved Architectural Decisions

1. Use `organizations` table for multi-tenancy
2. Keep `audit_projects` temporarily for backward compatibility
3. Store module catalog in PostgreSQL
4. Use additive migration strategy (no table renames)
5. Keep existing APIs during transition
6. Gradually migrate toward generic module APIs
7. Tenant isolation via `organization_id` everywhere

## Document Inventory (31 files)

### Architecture (`architecture/`)
| File | Topic |
|------|-------|
| [01_SYSTEM_ARCHITECTURE.md](./architecture/01_SYSTEM_ARCHITECTURE.md) | Overall system design |
| [02_SAAS_ARCHITECTURE.md](./architecture/02_SAAS_ARCHITECTURE.md) | SaaS platform layers |
| [03_MULTI_TENANT_ARCHITECTURE.md](./architecture/03_MULTI_TENANT_ARCHITECTURE.md) | Tenant isolation design |
| [04_NAVIGATION_STRUCTURE.md](./architecture/04_NAVIGATION_STRUCTURE.md) | UI navigation map |
| [05_USER_FLOW.md](./architecture/05_USER_FLOW.md) | End-to-end user journeys |
| [06_FOLDER_STRUCTURE.md](./architecture/06_FOLDER_STRUCTURE.md) | Codebase layout |

### Database (`database/`)
| File | Topic |
|------|-------|
| [01_DATABASE_DESIGN.md](./database/01_DATABASE_DESIGN.md) | Schema design |
| [02_ER_DIAGRAM.md](./database/02_ER_DIAGRAM.md) | Entity-relationship diagram |
| [03_TABLE_RELATIONSHIPS.md](./database/03_TABLE_RELATIONSHIPS.md) | FK and join paths |
| [04_MIGRATION_STRATEGY.md](./database/04_MIGRATION_STRATEGY.md) | Additive migration plan |

### API (`api/`)
| File | Topic |
|------|-------|
| [01_API_ARCHITECTURE.md](./api/01_API_ARCHITECTURE.md) | API design principles |
| [02_EXISTING_APIS.md](./api/02_EXISTING_APIS.md) | Current endpoint inventory |
| [03_FUTURE_GENERIC_MODULE_API.md](./api/03_FUTURE_GENERIC_MODULE_API.md) | Generic module API target |

### Business (`business/`)
| File | Topic |
|------|-------|
| [01_SUBSCRIPTION_MODEL.md](./business/01_SUBSCRIPTION_MODEL.md) | Plans and limits |
| [02_ORGANIZATION_MODEL.md](./business/02_ORGANIZATION_MODEL.md) | Audit firm tenancy |
| [03_MODULE_CATALOG.md](./business/03_MODULE_CATALOG.md) | 22-module catalog |
| [04_ENGAGEMENT_MODEL.md](./business/04_ENGAGEMENT_MODEL.md) | Engagement lifecycle |

### Roadmap (`roadmap/`)
| File | Topic |
|------|-------|
| [PHASE0_ARCHITECTURE.md](./roadmap/PHASE0_ARCHITECTURE.md) | Documentation phase (complete) |
| [PHASE1_SAAS_FOUNDATION.md](./roadmap/PHASE1_SAAS_FOUNDATION.md) | Multi-tenant foundation |
| [PHASE2_ENTERPRISE_WORKFLOW.md](./roadmap/PHASE2_ENTERPRISE_WORKFLOW.md) | Workflow & evidence |
| [PHASE3_AI_AND_SCALABILITY.md](./roadmap/PHASE3_AI_AND_SCALABILITY.md) | AI & scale |
| [IMPLEMENTATION_ROADMAP.md](./roadmap/IMPLEMENTATION_ROADMAP.md) | Summary timeline |

### ADRs (`adr/`)
| File | Decision |
|------|----------|
| [ADR-001-Organizations.md](./adr/ADR-001-Organizations.md) | Organizations as tenant root |
| [ADR-002-Module-Catalog.md](./adr/ADR-002-Module-Catalog.md) | Catalog in PostgreSQL |
| [ADR-003-Tenant-Isolation.md](./adr/ADR-003-Tenant-Isolation.md) | organization_id isolation |
| [ADR-004-Module-Enablement.md](./adr/ADR-004-Module-Enablement.md) | Per-engagement modules |
| [ADR-005-API-Strategy.md](./adr/ADR-005-API-Strategy.md) | Gradual generic API |
| [ADR-006-Migration-Strategy.md](./adr/ADR-006-Migration-Strategy.md) | Additive migrations |

### Status (`status/`)
| File | Topic |
|------|-------|
| [PROJECT_STATUS.md](./status/PROJECT_STATUS.md) | Current state snapshot |
| [CHANGELOG.md](./status/CHANGELOG.md) | Version history |
| [NEXT_STEPS.md](./status/NEXT_STEPS.md) | Immediate and phased tasks |

## Readiness Scores (June 2026)

| Metric | Score |
|--------|------:|
| Enterprise Readiness | 39 / 100 |
| SaaS Readiness | 24 / 100 |
| Documentation | 95 / 100 |

---

*Last updated: June 7, 2026 — Phase 0 complete. Awaiting approval before Phase 1 implementation.*
