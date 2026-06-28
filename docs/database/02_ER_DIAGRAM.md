# 02 — ER Diagram

## Purpose

Logical entity-relationship diagrams for current schema and target SaaS schema.

## Current ER Diagram

```mermaid
erDiagram
    users ||--o{ refresh_tokens : has
    users ||--o{ clients : owns
    clients ||--o{ audit_engagements : has
    audit_engagements ||--o{ audit_projects : has

    audit_projects ||--o{ journal_entries : contains
    audit_projects ||--o{ rule_results : contains
    audit_projects ||--o{ risk_scores : contains
    audit_projects ||--o{ revenue_invoices : contains
    audit_projects ||--o{ revenue_rule_results : contains
    audit_projects ||--o{ revenue_risk_scores : contains
    audit_projects ||--o{ procurement_invoices : contains
    audit_projects ||--o{ procurement_rule_results : contains
    audit_projects ||--o{ procurement_risk_scores : contains
    audit_projects ||--o{ audit_findings : contains
    audit_projects ||--o{ reports : contains

    journal_entries ||--o| risk_scores : scored_by
    rules_master ||--o{ rule_results : defines

    users {
        uuid id PK
        string email UK
        string role
        string company_name
        boolean is_active
    }

    clients {
        uuid id PK
        uuid user_id FK
        string name
        string status
    }

    audit_engagements {
        uuid id PK
        uuid client_id FK
        string financial_year
        date financial_year_end
        decimal large_value_threshold
    }

    audit_projects {
        uuid id PK
        uuid engagement_id FK
        string project_type
        string status
        int total_entries
    }

    audit_findings {
        uuid id PK
        uuid project_id FK
        string rule_code
        string risk_level
        jsonb journal_entry_ids
    }

    rules_master {
        uuid id PK
        string rule_code UK
        jsonb config_schema
        int default_score
    }
```

## Target SaaS ER Diagram

```mermaid
erDiagram
    subscription_plans ||--o{ organization_subscriptions : offers
    organizations ||--o| organization_subscriptions : has_active
    organizations ||--o{ organization_members : has
    users ||--o{ organization_members : belongs_to
    organizations ||--o{ clients : owns
    clients ||--o{ audit_engagements : has
    audit_engagements ||--o{ engagement_team_members : staffed_by
    audit_engagements ||--o{ engagement_enabled_modules : enables
    audit_module_catalog ||--o{ engagement_enabled_modules : referenced_by
    engagement_enabled_modules ||--o{ module_analysis_runs : executes
    module_analysis_runs ||--o{ audit_findings : produces
    audit_findings ||--o{ evidence_links : has
    evidence ||--o{ evidence_links : linked
    audit_findings ||--o{ review_comments : has
    audit_findings ||--o{ approvals : has
    audit_engagements ||--o{ workpapers : contains
    audit_engagements ||--o{ reports : has
    reports ||--o{ report_history : versions
    organizations ||--o{ audit_logs : tracks
    organizations ||--o{ usage_records : meters

    organizations {
        uuid id PK
        string name
        string slug UK
        string status
    }

    subscription_plans {
        uuid id PK
        string code UK
        int max_users
        int max_clients
        jsonb enabled_module_codes
    }

    audit_module_catalog {
        uuid id PK
        string code UK
        string name
        string status
    }

    engagement_enabled_modules {
        uuid engagement_id FK
        uuid module_id FK
        string status
    }
```

## Relationship Summary

| From | To | Current | Target |
|------|-----|:---:|:---:|
| User | Client | 1:N direct | N:M via org |
| Organization | Client | — | 1:N |
| Engagement | Module | via project_type | N:M enablement |
| Finding | Evidence | — | N:M |
| Finding | Workpaper | — | N:1 or N:M |

## Current Implementation

- ER centered on `audit_projects` as module container
- No organization, subscription, or catalog entities in DB

## Future Design

- Engagement becomes module orchestrator
- `audit_projects` retained for legacy data reads only
- Findings linked to `module_analysis_runs` for versioning

## Migration Strategy

Map legacy relationships:

```
audit_projects.project_type  →  engagement_enabled_modules.module_code
audit_projects.id            →  module_analysis_runs.legacy_project_id (nullable)
```

## Risks

Dual model during migration (projects + enabled modules) causes confusion if not documented.

## Recommendations

Publish ER v2 before Phase 1 migration scripts are written.

---

*Related: [03_TABLE_RELATIONSHIPS.md](./03_TABLE_RELATIONSHIPS.md)*
