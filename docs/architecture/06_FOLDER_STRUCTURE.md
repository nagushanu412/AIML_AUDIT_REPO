# 06 — Folder Structure

## Purpose

Document repository layout for frontend, backend, documentation, and key conventions.

## Repository Root

```
auditai-login/
├── app/                    Next.js App Router pages
├── components/             React components
├── lib/                    Shared TS utilities, API client, auth
├── docs/                   Project documentation (this folder)
├── database/               Sample Excel files for testing
├── backend/                FastAPI Python application
├── public/                 Static assets
├── package.json            Frontend dependencies (v0.1.0)
├── vercel.json             Vercel deployment config
├── DEPLOYMENT.md             Deploy runbook
└── README.md               Quick start
```

## Frontend — `app/`

```
app/
├── page.tsx                      Login
├── layout.tsx                    Root layout
├── register/ signup/             Registration
├── forgot-password/              Password reset UI
├── api/auth/                     Next.js auth route stubs
└── dashboard/
    ├── layout.tsx                AuthProvider + DashboardAuthGate
    ├── page.tsx                  Dashboard overview
    ├── clients/                  Client CRUD page
    ├── engagements/              Engagement CRUD page
    ├── projects/                 Project CRUD page
    ├── rules/                    Rules master editor
    ├── reports/                  Reports list
    ├── documents/                Reports list (duplicate)
    ├── settings/                 User profile
    └── ai-modules/
        ├── page.tsx              Catalog + workstreams
        ├── journal-entry-testing/
        ├── revenue-testing/
        ├── procurement-testing/
        └── [slug]/               Placeholder module pages
```

## Frontend — `components/`

```
components/
├── auth/                         Login, register, auth gate
├── dashboard/                    Shell, sidebar, lists, charts
├── ui/                           Button, Input, Spinner, Checkbox
├── journal-entry-testing/        JE workspace + shared SectionCard
├── revenue-testing/              Revenue workspace (enterprise UI)
├── procurement-testing/          Procurement workspace (enterprise UI)
└── audit-workstreams/            Legacy ProjectTypeWorkspace stub
```

## Frontend — `lib/`

```
lib/
├── api/                          apiFetch, types, endpoint functions
├── auth/                         Session, roles, AuthProvider
├── dashboard/                    modules.ts, navigation, projectModuleMap
├── journal-entry-testing/        Constants, types, utils
├── revenue-testing/              Constants, types
├── procurement-testing/          Constants, types
└── utils/                        cn() helper
```

## Backend — `backend/`

```
backend/
├── app/
│   ├── main.py                   FastAPI app (v2.0.0)
│   ├── config.py                 Settings from env
│   ├── database.py               SQLAlchemy engine
│   ├── deps.py                   get_current_user, get_current_auditor
│   ├── models/
│   │   └── audit.py              All 17 ORM models
│   ├── routers/                  13 API routers
│   ├── schemas/                  Pydantic models
│   └── services/                 Business logic
│       ├── rule_engine.py        Journal rules
│       ├── revenue_rule_engine.py
│       ├── procurement_rule_engine.py
│       ├── *_risk_scoring.py
│       ├── *_findings_service.py
│       ├── report_export.py
│       ├── auth_service.py
│       ├── project_access.py
│       └── seed_service.py
├── alembic/versions/             001–006 migrations
├── tests/                        Unit tests (journal + partial revenue)
├── requirements.txt
├── start.sh                      Migrations + uvicorn
├── railway.toml
└── Dockerfile
```

## Documentation — `docs/`

```
docs/
├── README.md
├── ENTERPRISE_SAAS_ARCHITECTURE_REVIEW.md
├── architecture/     (6 files)
├── database/         (4 files)
├── api/              (3 files)
├── business/         (4 files)
├── roadmap/          (5 files)
├── adr/              (6 ADRs)
└── status/           (3 files)
```

## Current Implementation

- Monorepo: frontend at root, backend in `backend/`
- No shared package between FE/BE (API contract via OpenAPI + TS types manually)
- Module workspaces duplicated across 3 folders (technical debt)

## Future Design

```
backend/app/modules/              Plugin registry per catalog module
components/audit-module/          Shared workspace shell
lib/module-registry/              Module config from API
```

## Advantages

- Clear FE/BE split
- Co-located docs with code
- Alembic migrations versioned with backend

## Disadvantages

- Triplicated workspace components
- `journal-entry-testing/` folder used as shared UI namespace
- Catalog in TS not synced with backend

## Migration Strategy

- Phase 1: Add `docs/` references in README (optional)
- Phase 2: Consolidate workspace components without moving routes
- Phase 3: Backend module plugin folder structure

## Risks

- Folder sprawl as 22 modules are added
- Import coupling from revenue/procurement → journal-entry-testing components

## Recommendations

1. Create shared `components/audit-shared/` in Phase 2 refactor (document first)
2. Move `SectionCard` out of journal-entry-testing namespace
3. Generate TS types from OpenAPI in future

---

*Related: [01_SYSTEM_ARCHITECTURE.md](./01_SYSTEM_ARCHITECTURE.md)*
