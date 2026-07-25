# Remediation Milestones 1–4 — URL Manual Test Cases

Use these against a running API (`http://127.0.0.1:8000`).  
Interactive UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**Demo login (seeded):**
- Email: `auditor@demo.auditai.com`
- Password: `AuditAI2026!`

Replace placeholders like `{project_id}`, `{engagement_id}`, `{finding_id}` with values from list responses.

---

## 0 — Setup (all milestones)

### TC-0.1 Health
| | |
|---|---|
| **Method / URL** | `GET /health` |
| **Auth** | none |
| **Expect** | `200` — `"status": "ok"` |

### TC-0.2 Login
| | |
|---|---|
| **Method / URL** | `POST /auth/login` |
| **Body** | `{"email":"auditor@demo.auditai.com","password":"AuditAI2026!"}` |
| **Expect** | `200` — `access_token`, `organization_id` present |

Save header for later calls:
```http
Authorization: Bearer <access_token>
```

### TC-0.3 Resolve IDs
| Step | Method / URL | Expect |
|------|----------------|--------|
| Clients | `GET /clients` | `200` list — pick `client_id` |
| Engagements | `GET /engagements` | `200` — pick `engagement_id` |
| Projects | `GET /projects` | `200` — pick journal / revenue / procurement `project_id` by `project_type` |

---

## Milestone 1 — Tenant isolation

Goal: Org A must not read Org B’s clients / engagements / projects / findings.

### TC-M1.1 Own org data visible
| | |
|---|---|
| **Method / URL** | `GET /clients` |
| **Auth** | Demo token |
| **Expect** | `200` — only your org’s clients (non-empty for demo) |

### TC-M1.2 Cross-tenant engagement denied
| | |
|---|---|
| **Method / URL** | `GET /engagements/{other_org_engagement_id}` |
| **Auth** | Demo token |
| **How to get other ID** | Register a second user/org (below), create an engagement there, copy its id, then call with **demo** token |
| **Expect** | `403` or `404` (not `200` with foreign data) |

### TC-M1.3 Cross-tenant project denied
| | |
|---|---|
| **Method / URL** | `GET /projects/{other_org_project_id}` |
| **Auth** | Demo token |
| **Expect** | `403` or `404` |

### TC-M1.4 Cross-tenant findings list denied
| | |
|---|---|
| **Method / URL** | `GET /engagements/{other_org_engagement_id}/findings` |
| **Auth** | Demo token |
| **Expect** | `403` or `404` — must not return other org findings |

### TC-M1.5 Create second org (for cross-tenant IDs)
| Step | Method / URL | Body |
|------|----------------|------|
| Register | `POST /auth/register` | `{"email":"firmb@example.com","password":"TestPass123!","full_name":"Firm B"}` (fields per `/docs`) |
| Create org | `POST /organizations` | org name payload per `/docs` |
| Create client | `POST /clients` | with Firm B token |
| Create engagement | `POST /engagements` | with Firm B token |

Then re-run TC-M1.2–M1.4 with Firm B resource IDs + **demo** token.

### TC-M1.6 Unauthenticated rejected
| | |
|---|---|
| **Method / URL** | `GET /clients` |
| **Auth** | none |
| **Expect** | `401` |

---

## Milestone 2 — Evidence gate (risk scoring blocked without evidence)

Goal: `run-risk` returns **400** when any finding on the project has zero `evidence_links`.

Prerequisite path (journal example):

1. `POST /upload?project_id={journal_project_id}` (multipart file) — or use existing uploaded data  
2. `POST /run-rules?project_id={journal_project_id}`  
3. `POST /generate-findings?project_id={journal_project_id}`  
4. Confirm findings: `GET /findings?project_id={journal_project_id}`

### TC-M2.1 Block risk when findings lack evidence (Journal legacy)
| | |
|---|---|
| **Method / URL** | `POST /run-risk?project_id={journal_project_id}` |
| **Auth** | Demo token |
| **Setup** | Project has at least one finding with no evidence link |
| **Expect** | `400` — detail mentions evidence / EvidenceGate |

### TC-M2.2 Block risk (Revenue legacy)
| | |
|---|---|
| **Method / URL** | `POST /revenue/run-risk?project_id={revenue_project_id}` |
| **Expect** | `400` if bare findings exist |

### TC-M2.3 Block risk (Procurement legacy)
| | |
|---|---|
| **Method / URL** | `POST /procurement/run-risk?project_id={procurement_project_id}` |
| **Expect** | `400` if bare findings exist |

### TC-M2.4 Block risk (generic module API)
| Module | Method / URL |
|--------|----------------|
| Journal | `POST /modules/JOURNAL_ENTRY_TESTING/run-risk` body `{"project_id":"..."}` |
| Revenue | `POST /modules/REVENUE_TESTING/run-risk` body `{"project_id":"..."}` |
| Procurement | `POST /modules/PROCUREMENT_TESTING/run-risk` body `{"project_id":"..."}` |
| **Expect** | `400` when findings lack evidence links |

(Confirm exact JSON body shape in `/docs` under Generic Modules.)

### TC-M2.5 Allow risk after linking evidence
| Step | Method / URL | Notes |
|------|----------------|--------|
| List / create evidence | `GET /engagements/{engagement_id}/evidence` or `POST /engagements/{engagement_id}/evidence` | multipart upload |
| Link to finding | `POST /engagements/{engagement_id}/evidence/{evidence_id}/links` | see body below |
| Re-run risk | `POST /run-risk?project_id={project_id}` | **Expect `200`** |

**Link body example:**
```json
{
  "linked_entity_type": "finding",
  "linked_entity_id": "{finding_id}",
  "finding_id": "{finding_id}",
  "link_type": "supports",
  "notes": "M2 evidence gate test"
}
```

Repeat link for **every** finding on that project (gate fails if any finding has zero links).

---

## Milestone 3 — Auditor decision clarity (`reviewed_by` / `reviewed_at` + history)

Use finding lifecycle APIs (not the short `FindingOut` from `/findings?project_id=`).

### TC-M3.1 List engagement findings
| | |
|---|---|
| **Method / URL** | `GET /engagements/{engagement_id}/findings` |
| **Expect** | `200` — items include `status`, `reviewed_by`, `reviewed_at` |

### TC-M3.2 Open → under_review leaves reviewed null
| | |
|---|---|
| **Method / URL** | `PATCH /findings/{finding_id}/status` |
| **Body** | `{"status":"under_review","change_reason":"M3 test"}` |
| **Expect** | `200` — `status=under_review`, `reviewed_by=null`, `reviewed_at=null` |

### TC-M3.3 Decision status stamps reviewer
| | |
|---|---|
| **Method / URL** | `PATCH /findings/{finding_id}/status` |
| **Body** | `{"status":"cleared","change_reason":"No exception"}` |
| **Auth** | Partner / audit_manager / reviewer role (demo must have approve role) |
| **Expect** | `200` — `status=cleared`, **both** `reviewed_by` and `reviewed_at` set |

Also try `accepted` or `closed` the same way.

### TC-M3.4 Reopen clears stamps
| | |
|---|---|
| **Method / URL** | `PATCH /findings/{finding_id}/status` |
| **Body** | `{"status":"open","change_reason":"Reopen for rework"}` |
| **Expect** | `200` — `status=open`, `reviewed_by=null`, `reviewed_at=null` |

### TC-M3.5 Status history written
| | |
|---|---|
| **Method / URL** | `GET /findings/{finding_id}/history` |
| **Expect** | `200` — rows with `action` (`status_change` / `reopened`), `new_status`, `changed_by` |

### TC-M3.6 Partner approval path (history + accepted + reviewed_*)
| Step | Method / URL | Body | Expect |
|------|----------------|------|--------|
| Put finding in `open` or `under_review` | `PATCH /findings/{id}/status` | `{"status":"under_review"}` | `200` |
| Request approval | `POST /findings/{finding_id}/approve` | `{"comments":"Please approve"}` | `201` — note `approval_id` |
| Partner decide | `PATCH /approvals/{approval_id}` | `{"status":"approved","comments":"OK"}` | `200` |
| Verify finding | `GET /findings/{finding_id}` | — | `status=accepted`, `reviewed_by`/`reviewed_at` set |
| Verify history | `GET /findings/{finding_id}/history` | — | row `new_status=accepted`, `action=status_change` |

---

## Milestone 4 — Cleanup (`source_record_ids` + `rule_content_version`)

### Note on `source_record_ids`
This field is **not** returned by legacy `GET /findings?project_id=` (`FindingOut`).  
It is an internal/DB column rename. URL checks for M4 focus on **`rule_content_version`**.  
To confirm rename locally: DB column `audit_findings.source_record_ids` exists; `journal_entry_ids` does not.

### TC-M4.1 Rules expose `rule_content_version`
| | |
|---|---|
| **Method / URL** | `GET /rules` |
| **Expect** | `200` — each rule has `rule_content_version` (integer ≥ 1) |

### TC-M4.2 Bump rule content version
| | |
|---|---|
| **Method / URL** | `PATCH /rules/{rule_id}` |
| **Body** | `{"description":"M4 URL test bump"}` |
| **Expect** | `200` — `rule_content_version` increased by 1 vs previous GET |

### TC-M4.3 New findings stamp current version (Journal)
| Step | Method / URL | Expect |
|------|----------------|--------|
| Note rule version | `GET /rules` — e.g. `LARGE_VALUE` → `v` | remember `v` |
| Generate | `POST /generate-findings?project_id={journal_project_id}` | `200` list |
| Open lifecycle finding | `GET /engagements/{engagement_id}/findings?project_id={journal_project_id}` | item for that rule has `rule_content_version == v` |

### TC-M4.4 Revenue / Procurement stamp
| Module | Generate | List lifecycle |
|--------|----------|----------------|
| Revenue | `POST /revenue/generate-findings?project_id={revenue_project_id}` | `GET /engagements/{engagement_id}/findings?project_id={revenue_project_id}` |
| Procurement | `POST /procurement/generate-findings?project_id={procurement_project_id}` | same with procurement project |

**Expect:** new findings show `rule_content_version` matching the rule’s current version from `GET /rules`.

### TC-M4.5 Prior stamp unchanged after bump + regenerate elsewhere
| Step | Action |
|------|--------|
| 1 | Pick finding A on project P1 with `rule_content_version = 1` (or current). Record `finding_id` + version. |
| 2 | `PATCH /rules/{rule_id}` → version becomes `2` (or N+1). |
| 3 | Generate findings on a **different** project P2 (same rule family). |
| 4 | `GET /findings/{finding_A_id}` → still old version. |
| 5 | New finding on P2 → new version. |

> Regenerating on the **same** project deletes/recreates that project’s findings — use a second project for the “prior unchanged” check.

### TC-M4.6 Generic module generate (optional)
| | |
|---|---|
| **Method / URL** | `POST /modules/JOURNAL_ENTRY_TESTING/generate-findings` |
| **Body** | `{"project_id":"{journal_project_id}"}` |
| **Then** | `GET /findings/{id}` or engagement findings list — check `rule_content_version` |

---

## Quick curl cheat sheet

```bash
BASE=http://127.0.0.1:8000

# Login
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"auditor@demo.auditai.com","password":"AuditAI2026!"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Auth header helper
AUTH="Authorization: Bearer $TOKEN"

# M1
curl -s -H "$AUTH" "$BASE/clients"

# M2 (expect 400 if bare findings)
curl -s -X POST -H "$AUTH" "$BASE/run-risk?project_id=YOUR_PROJECT_ID"

# M3
curl -s -X PATCH -H "$AUTH" -H "Content-Type: application/json" \
  "$BASE/findings/YOUR_FINDING_ID/status" \
  -d '{"status":"cleared","change_reason":"URL test"}'

# M4
curl -s -H "$AUTH" "$BASE/rules"
```

---

## Pass / fail checklist

| ID | Milestone | Pass? |
|----|-----------|-------|
| TC-M1.1–M1.6 | Tenant isolation | |
| TC-M2.1–M2.5 | Evidence gate | |
| TC-M3.1–M3.6 | Reviewed stamps + history + partner approve | |
| TC-M4.1–M4.6 | Rule content version | |

Swagger: open `/docs`, Authorize with Bearer token, run the same paths interactively.
