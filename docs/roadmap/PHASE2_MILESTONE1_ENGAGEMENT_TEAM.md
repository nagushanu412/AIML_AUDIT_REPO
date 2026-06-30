# Phase 2 Milestone 1 — Engagement Team Management

**Status:** Complete  
**Migration:** `014_engagement_team_members`  
**Date:** 2026-06-07

## Scope

Enterprise engagement team assignment with role-based permissions, assignment history, and audit logging.

## Database

| Table | Purpose |
|-------|---------|
| `engagement_team_members` | Active team roster per engagement |
| `engagement_team_assignment_history` | Immutable assignment change log |

### Engagement team roles

- `partner` — single slot per engagement
- `audit_manager` — single slot per engagement
- `senior_auditor` — multiple allowed
- `auditor` — multiple allowed
- `reviewer` — multiple allowed

### Constraints

- Unique `(engagement_id, user_id)` — one assignment row per user
- Assignee must be an active organization member (not `client_user` / `read_only`)
- Org role eligibility enforced per engagement role
- Partner and audit manager slots limited to one active member each

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/engagements/{id}/team` | List team (search, role filter, pagination) |
| GET | `/engagements/{id}/team/summary` | Partner, manager, counts by role |
| POST | `/engagements/{id}/team` | Assign or reactivate member |
| PATCH | `/engagements/{id}/team/{member_id}` | Update role or notes |
| DELETE | `/engagements/{id}/team/{member_id}` | Soft-remove member |
| GET | `/engagements/{id}/team/history` | Assignment history with filters |

## RBAC

**Manage team:** `organization_owner`, `partner`, `audit_manager`  
**View team:** Any user with engagement tenant access

## Audit Logging

Actions logged to `audit_logs`:

- `team.assign`
- `team.update`
- `team.remove`

Assignment changes also recorded in `engagement_team_assignment_history`.

## Frontend

- **Engagements** page → expand row → **Team** panel
- Assign from organization members, change roles, remove members
- Search, role filter, assignment history viewer

## Manual Test Checklist

1. Log in as audit manager or partner
2. Open **Engagements** → click **Team** on an engagement
3. Assign an auditor and a reviewer
4. Assign engagement partner (org partner only)
5. Attempt duplicate partner → expect error
6. Change auditor to senior auditor
7. Remove a member → verify history entry
8. Log in as auditor → verify read-only (no assign form)

## Regression

All Phase 1 tests must continue to pass after migration `014`.

---

*Next milestone: Workpapers & Evidence Repository (Milestone 2)*
