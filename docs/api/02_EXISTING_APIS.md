# 02 — Existing APIs

## Purpose

Complete inventory of implemented FastAPI endpoints as of API version 2.0.0.

**Base URL (production):** `https://aiml-audit-api-production.up.railway.app`

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service status |
| GET | `/health/db` | Database connectivity |

## Authentication — `/auth`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create user (role=auditor) |
| POST | `/auth/login` | Issue access + refresh tokens |
| POST | `/auth/refresh` | Rotate tokens |
| POST | `/auth/logout` | Revoke refresh token |
| POST | `/auth/forgot-password` | Stub (no email flow) |
| GET | `/auth/me` | Current user profile |

## Organizations — `/organizations` *(Phase 1 Milestone 1)*

| Method | Path | Description |
|--------|------|-------------|
| POST | `/organizations` | Create audit firm organization; links `users.default_organization_id` |
| GET | `/organizations/me` | Get current user's organization |
| PATCH | `/organizations/me` | Update current user's organization |
| GET | `/organizations/{organization_id}` | Get organization (must match user's default org) |
| PATCH | `/organizations/{organization_id}` | Update organization (must match user's default org) |
| DELETE | `/organizations/{organization_id}` | Close organization (status → `closed`) |

All organization endpoints require Bearer authentication.

## Organization Members — `/organizations/*/members` *(Phase 1 Milestone 3)*

| Method | Path | Description |
|--------|------|-------------|
| GET | `/organizations/me/members` | List members of current user's organization |
| POST | `/organizations/me/members/invite` | Invite user by email (`email`, `role`, optional `full_name`) |
| PATCH | `/organizations/me/members/{member_id}` | Update member role or status |
| DELETE | `/organizations/me/members/{member_id}` | Remove (disable) member |
| GET | `/organizations/{organization_id}/members` | List members (org-scoped) |
| POST | `/organizations/{organization_id}/members/invite` | Invite member |
| PATCH | `/organizations/{organization_id}/members/{member_id}` | Update member |
| DELETE | `/organizations/{organization_id}/members/{member_id}` | Remove member |

Roles: `organization_owner`, `partner`, `audit_manager`, `senior_auditor`, `auditor`, `reviewer`, `client_user`, `read_only`.

Member statuses: `active`, `invited`, `disabled`.

RBAC: owners and audit managers can invite/remove/update; partners and auditors can list members.

## Subscriptions — `/subscriptions` *(Phase 1 Milestone 2)*

| Method | Path | Description |
|--------|------|-------------|
| GET | `/subscriptions/plans` | List active plans (Free, Starter, Professional, Enterprise) |
| GET | `/subscriptions/me` | Current org subscription, plan limits, and usage snapshot |
| PATCH | `/subscriptions/me` | Change plan manually (`{ "plan_code": "starter" }`) |

All subscription endpoints require Bearer authentication and an organization linked to the user.

## Clients — `/clients`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/clients` | List user's clients |
| POST | `/clients` | Create client |
| GET | `/clients/{client_id}` | Get client |
| PATCH | `/clients/{client_id}` | Update client |
| DELETE | `/clients/{client_id}` | Delete client (+ cascades) |

## Engagements — `/engagements`

| Method | Path | Query | Description |
|--------|------|-------|-------------|
| GET | `/engagements` | `client_id` | List engagements |
| POST | `/engagements` | — | Create engagement |
| GET | `/engagements/{id}` | — | Get engagement |
| PATCH | `/engagements/{id}` | — | Update engagement |
| DELETE | `/engagements/{id}` | — | Delete engagement |

## Projects — `/projects`

| Method | Path | Query | Description |
|--------|------|-------|-------------|
| GET | `/projects` | `engagement_id` | List projects |
| POST | `/projects` | — | Create project |
| GET | `/projects/{id}` | — | Get project |
| PATCH | `/projects/{id}` | — | Update project |
| DELETE | `/projects/{id}` | — | Delete project |

## Journal Entry Testing

| Method | Path | Query | Description |
|--------|------|-------|-------------|
| POST | `/upload` | `project_id` | Upload journal Excel |
| POST | `/run-rules` | `project_id` | Run 7 journal rules |
| GET | `/rule-results` | `project_id`, filters | List rule results |
| POST | `/run-risk` | `project_id` | Score all entries |
| GET | `/risk-scores` | `project_id`, filters | List risk scores |
| POST | `/generate-findings` | `project_id` | Create findings |
| GET | `/findings` | `project_id` | List findings |

## Journal Reports — root analytics router

| Method | Path | Description |
|--------|------|-------------|
| GET | `/reports` | List reports (`project_id`) |
| POST | `/reports/generate` | Generate report |
| GET | `/reports/{id}/download` | Download file |

Report types: `journal_audit_excel`, `journal_audit_pdf`, `journal_working_paper`, etc.

## Revenue Testing — `/revenue`

| Method | Path | Query |
|--------|------|-------|
| POST | `/revenue/upload` | `project_id` |
| POST | `/revenue/run-rules` | `project_id` |
| POST | `/revenue/run-risk` | `project_id` |
| GET | `/revenue/risk-scores` | `project_id`, pagination |
| POST | `/revenue/generate-findings` | `project_id` |
| GET | `/revenue/findings` | `project_id` |

Requires `project_type = revenue_testing`.

## Procurement Testing — `/procurement`

| Method | Path | Query |
|--------|------|-------|
| POST | `/procurement/upload` | `project_id` |
| POST | `/procurement/run-rules` | `project_id` |
| POST | `/procurement/run-risk` | `project_id` |
| GET | `/procurement/risk-scores` | `project_id`, pagination |
| POST | `/procurement/generate-findings` | `project_id` |
| GET | `/procurement/findings` | `project_id` |

Requires `project_type = procurement_testing`.

## Rules Master — `/rules`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/rules` | List all rules |
| GET | `/rules/{rule_id}` | Get rule + config_schema |
| PATCH | `/rules/{rule_id}` | Update rule config |

## Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/summary` | KPIs (journal-focused) |

## Frontend API Client

Mapped in `lib/api/index.ts` — ~40 wrapper functions using `apiFetch` / `apiUpload`.

## Current Gaps

- No tenant isolation on clients/engagements — Milestone 4
- No module catalog endpoints — Milestone 5
- No evidence, workpaper, review, or audit log APIs
- Revenue/procurement use separate report generation via shared `/reports/generate` with type param
- No webhook or billing endpoints
- Subscription limit enforcement on write APIs — Milestone 8

## Recommendations

- Document OpenAPI as contract before Phase 1
- Add integration tests per router before tenant migration

---

*Related: [01_API_ARCHITECTURE.md](./01_API_ARCHITECTURE.md)*
