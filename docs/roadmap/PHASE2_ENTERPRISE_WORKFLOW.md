# Phase 2 — Enterprise Workflow

## Purpose

Add Big4-style audit execution: teams, evidence, workpapers, review, approvals, finding lifecycle, async analysis, blob storage.

## Duration (Estimate)

10–12 weeks

## Prerequisites

- Phase 1 complete and stable in production
- Tenant isolation verified

## Goals

1. Engagement team assignment
2. Evidence repository with file storage
3. Workpaper management
4. Finding lifecycle (Open → Review → Cleared/Accepted)
5. Review comments and partner approval
6. Async module analysis jobs
7. Engagement-centric module launcher
8. Consolidated engagement report

## Database Deliverables

| Table | Purpose |
|-------|---------|
| `engagement_team_members` | Team roles per engagement |
| `workpapers` | Workpaper index |
| `evidence` | File metadata + storage key |
| `evidence_links` | Link evidence to findings |
| `review_comments` | Threaded review |
| `approvals` | Sign-off records |
| `finding_status_history` | Lifecycle audit |
| `module_analysis_runs` | Job tracking |
| `report_history` | Report versioning |

## Backend Deliverables

| Item | Description |
|------|-------------|
| S3/R2 storage adapter | Reports + evidence |
| Celery/RQ workers | Async run-rules/risk |
| `/evidence/*` | Upload, link, download |
| `/workpapers/*` | CRUD |
| `/findings/{id}/comments` | Review API |
| `/findings/{id}/approve` | Approval API |
| `/analysis/runs/*` | Job status |
| Consolidated report generator | Cross-module engagement PDF |

## Frontend Deliverables

| Item | Description |
|------|-------------|
| Engagement hub page | Central workspace |
| Enabled modules only | Hide non-enabled |
| Finding drill-down drawer | Source transactions |
| Evidence upload panel | Attach to findings |
| Review / approve UI | Role-gated |
| Async progress indicator | Job polling |
| Deprecate workstreams panel | Redirect to engagement hub |

## Exit Criteria

- [ ] Auditor attaches evidence to finding
- [ ] Reviewer adds comment; partner approves
- [ ] Analysis run >10k rows completes via background job
- [ ] Reports stored in blob (survive redeploy)
- [ ] Audit log captures review actions

## Out of Scope (Phase 2)

- LLM narratives
- Modules 4–22 implementation
- Stripe automation
- Sampling / materiality engine

## Risks

| Risk | Mitigation |
|------|------------|
| Blob storage cost | Plan storage limits from Phase 1 |
| Job queue ops | Railway Redis add-on |

## Recommendations

- Launch engagement hub to pilot firms before removing old nav
- PDF report includes sign-off block

---

*Related: [PHASE3_AI_AND_SCALABILITY.md](./PHASE3_AI_AND_SCALABILITY.md)*
