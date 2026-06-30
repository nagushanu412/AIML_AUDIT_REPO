# 02 — Organization Model

## Purpose

Define the audit firm (organization) entity, membership, roles, and how it replaces user-owned data in the target SaaS model.

## Approved Decision

> Use organizations table. Use organization_id everywhere.

See [../adr/ADR-001-Organizations.md](../adr/ADR-001-Organizations.md).

## Organization Entity (Target)

| Field | Description |
|-------|-------------|
| `id` | UUID primary key |
| `name` | Legal / trading name (e.g. "ABC & Co Chartered Accountants") |
| `slug` | URL-safe unique identifier |
| `status` | `active`, `suspended`, `closed` |
| `settings` | JSONB — timezone, fiscal defaults, branding |
| `created_at` | Timestamp |

## Organization Contains (Target)

- Subscription (one active)
- Users (via membership)
- Clients (all audited entities)
- Usage metrics (storage, AI credits)
- Firm-wide settings and audit logs

## Organization Members (Target)

| Field | Description |
|-------|-------------|
| `organization_id` | FK |
| `user_id` | FK |
| `role` | See role table below |
| `status` | `active`, `invited`, `disabled` |
| `invited_at`, `joined_at` | Timestamps |

### Roles (Target)

| Role | Typical permissions |
|------|---------------------|
| Organization Owner | Billing, delete org, all admin |
| Partner | Approve findings, view all engagements |
| Audit Manager | Manage teams, enable modules |
| Senior Auditor | Run analysis, upload, draft findings |
| Auditor | Run analysis, upload |
| Reviewer | Comment, approve (no upload) |
| Client User | Read-only client portal |
| Read Only | View reports |

## Current Implementation

| Aspect | Current (after Milestone 3) |
|--------|----------------------------|
| Organization table | ✓ `organizations` (Alembic 007) |
| User ↔ org link | ✓ `organization_members` + interim `users.default_organization_id` |
| Organization API | ✓ `/organizations/*` CRUD |
| Member API | ✓ `/organizations/*/members/*` invite, list, update, remove |
| Settings UI | ✓ Create/edit firm + team member management on `/dashboard/settings` |
| RBAC foundation | ✓ Org-scoped roles and permission matrix (enforcement expands in M4/M8) |
| `User.company_name` | Still present; not synced to org automatically |
| Client ownership | Still `clients.user_id` — Milestone 4 |
| Multi-user same firm | ✓ Via organization members (one org per user in Phase 1) |
| Registration | Creates user only; org created separately in Settings |

## Scale Targets

| Firms | Considerations |
|-------|------------------|
| 100 | Single DB, shared schema |
| 1,000 | Index on organization_id; connection pool tuning |
| 5,000 | Read replicas; blob storage |
| 10,000+ | Usage monitoring; optional shard planning |

## Future Design

### JWT claims (target)

```json
{
  "sub": "user_uuid",
  "org_id": "organization_uuid",
  "org_role": "AUDIT_MANAGER",
  "subscription_tier": "professional"
}
```

### Firm admin UI

- Invite user by email
- Assign role
- Deactivate member
- View subscription and usage

## Advantages

- Matches how CA firms actually operate
- Enables collaboration on same engagement
- Clear billing entity

## Disadvantages

- Users in multiple firms need multi-org membership (N:M)
- Role matrix complexity

## Migration Strategy

1. Create org per existing user from `company_name`
2. Set user as Organization Owner
3. Backfill `clients.organization_id`
4. New registration: create org + owner in one transaction

## Risks

| Risk | Mitigation |
|------|------------|
| Duplicate org names | Unique slug; admin merge tool later |
| User with no company_name | Default org name from email domain |

## Recommendations

- Support one org per user in Phase 1; multi-org in Phase 3
- Never expose sequential org IDs — UUID only
- Firm suspension cascades to read-only, not delete

---

*Related: [04_ENGAGEMENT_MODEL.md](./04_ENGAGEMENT_MODEL.md)*
