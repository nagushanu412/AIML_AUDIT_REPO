# AIML_AUDIT — Remediation Plan to 95+ (v2, corrected)

> **Correction notice (v2):** the original version of this plan wrongly treated Row-Level
> Security as an urgent Priority 0 gap. It isn't — ADR-003 already made a deliberate,
> documented decision to defer RLS to Phase 3. This version retracts that error and
> reframes Priority 0 around what's actually outstanding: completing `organization_id`
> coverage and the isolation test matrix, both already tracked in the existing roadmap.
> It also retracts the instruction to delete 3 module catalog entries — ADR-002 already
> settled that all 22 are real catalog modules. See
> `AIML_AUDIT_Product_Constitution_v2.4.docx` for the full reconciliation.

**Purpose:** the exact, concrete changes needed to close the gap between the current
79/100 implementation and a 95+ implementation. Each item states the problem, why it
matters, the specific fix, the files it touches, and how to prove it's actually done.

**How to use this with Cursor:** hand it one priority tier at a time, in order. Do not
start Priority 1 until every acceptance check in Priority 0 passes. Each item is written
so it can be pasted directly as a Cursor task.

---

## Priority 0 — Tenant Isolation Completeness
*Not urgent because of RLS — RLS is correctly deferred to Phase 3 per ADR-003. This is
Priority 0 because it's the last ~8% of Phase 1, already on your own roadmap in
`docs/status/PROJECT_STATUS.md`, and because Evidence Gate work (Priority 1) is easier
to verify correctly once every tenant table is consistent.*

### 0.1 Make `organization_id` non-nullable on `audit_engagements`

**Problem:** `audit_engagements.organization_id` is nullable, with `project_access.py`
falling back to `clients.organization_id` via `client_id` when it's null. Two possible
sources of truth for one tenant boundary means they can silently disagree.

**Fix:**
```sql
-- 1. Backfill any nulls from the client relationship
UPDATE audit_engagements e
SET organization_id = c.organization_id
FROM clients c
WHERE e.client_id = c.id
  AND e.organization_id IS NULL;

-- 2. Verify zero remain before proceeding
SELECT count(*) FROM audit_engagements WHERE organization_id IS NULL;
-- must return 0

-- 3. Enforce it going forward
ALTER TABLE audit_engagements
  ALTER COLUMN organization_id SET NOT NULL;
```

**Code change:** remove the client-fallback branch in `project_access.py`'s
`get_owned_project()` — it should only ever read `engagement.organization_id` after this.

**Acceptance:** `get_owned_project()` has no `clients.organization_id` fallback code path.
A test that creates an engagement without `organization_id` fails at the database level,
not the application level.

---

### 0.2 Denormalize `organization_id` onto every tenant-scoped table

**Problem:** `journal_entries`, `revenue_invoices`, `procurement_invoices`, `audit_findings`,
`rule_results` (and module equivalents), `risk_scores` (and module equivalents), and
`reports` only carry `project_id`. Row-Level Security needs a direct column to filter on —
multi-hop RLS (table → project → engagement → organization) is slow and easy to get wrong.

**Fix — for each tenant-scoped table:**
**Note (per Cursor's live-code audit):** `evidence`, `workpapers`, `audit_logs`,
`feature_flags`, `finding_relationships`, and `module_analysis_runs` already have a
nullable `organization_id` column — for these, skip the `ADD COLUMN` step and go
straight to backfill + `NOT NULL`. Also add `organization_id` to `evidence_links`,
`engagement_enabled_modules`, `engagement_team_members`, `review_comments`, and
`approvals`, which were missed in the original table list below.

```sql
ALTER TABLE journal_entries ADD COLUMN organization_id UUID;
ALTER TABLE revenue_invoices ADD COLUMN organization_id UUID;
ALTER TABLE procurement_invoices ADD COLUMN organization_id UUID;
ALTER TABLE audit_findings ADD COLUMN organization_id UUID;
ALTER TABLE rule_results ADD COLUMN organization_id UUID;
ALTER TABLE revenue_rule_results ADD COLUMN organization_id UUID;
ALTER TABLE procurement_rule_results ADD COLUMN organization_id UUID;
ALTER TABLE risk_scores ADD COLUMN organization_id UUID;
ALTER TABLE revenue_risk_scores ADD COLUMN organization_id UUID;
ALTER TABLE procurement_risk_scores ADD COLUMN organization_id UUID;
ALTER TABLE reports ADD COLUMN organization_id UUID;
ALTER TABLE evidence_links ADD COLUMN organization_id UUID;
ALTER TABLE engagement_enabled_modules ADD COLUMN organization_id UUID;
ALTER TABLE engagement_team_members ADD COLUMN organization_id UUID;
ALTER TABLE review_comments ADD COLUMN organization_id UUID;
ALTER TABLE approvals ADD COLUMN organization_id UUID;

-- backfill each from audit_projects -> audit_engagements
UPDATE journal_entries je
SET organization_id = e.organization_id
FROM audit_projects p JOIN audit_engagements e ON e.id = p.engagement_id
WHERE je.project_id = p.id;
-- repeat the same UPDATE pattern for every table above

-- for tables that already had a nullable organization_id (evidence, workpapers,
-- audit_logs, feature_flags, finding_relationships, module_analysis_runs):
-- backfill any remaining nulls the same way, then skip straight to NOT NULL below

-- then lock it down
ALTER TABLE journal_entries ALTER COLUMN organization_id SET NOT NULL;
-- repeat for every table above
```

**Keep it correct going forward — application-level, not just migration-level:**
Set `organization_id` at write time in the SQLAlchemy model layer (e.g. an
`before_insert` event listener that copies it from the parent project/engagement),
so no future code path can insert a row and forget it.

**Acceptance:** every table listed has a `NOT NULL organization_id` column, and a new
row cannot be inserted through the ORM without one being set automatically.

---

### 0.3 Write the Multi-Tenant Isolation Test Matrix (not RLS — see notice at top)

**This replaces the original 0.3, which told you to enable Row-Level Security here.**
That was wrong. ADR-003 deliberately deferred RLS to Phase 3, with real reasoning
(harder to debug, still needs the org_id column, application-layer checks are
sufficient for Phase 1). This Constitution (v2.4) now agrees with that decision.
Do not enable RLS as part of this priority tier — add it to the Phase 3 backlog instead.

**What actually belongs here:** per `docs/status/PROJECT_STATUS.md`'s own "Pending" list,
the real remaining Phase 1 item is the full multi-tenant HTTP isolation test matrix.

**Fix — add to the existing pytest suite (136 tests passing today), not a new one:**
For every module and every tenant-scoped table from 0.2, write a test that:
1. Creates two organizations (Firm A, Firm B) with one user each.
2. Firm A creates a record (journal entry, finding, evidence, report, etc.).
3. Firm B's authenticated token attempts to read/update/delete that record via the API.
4. Assert the response is 404 or 403 — never 200, and never a partial data leak in
   a list endpoint.

**Acceptance:** a test matrix covering every tenant-scoped table and every module's API
surface, added to the existing backend test suite, all passing.

---

## Priority 1 — Evidence Gate Enforcement (not table creation — the tables already exist)
*Do this after Priority 0. This is the single most-flagged gap across every prior review —
but it's smaller work than originally scoped, because the storage already exists.*

### 1.1 Use the existing `evidence` and `evidence_links` tables — do not create `evidence_records`

**Correction:** the original plan told you to create a new `evidence_records` table.
Don't — Cursor's live-code audit found `evidence` (with versioning: `root_evidence_id`,
`version_number`, `is_current`) and `evidence_links` (linking evidence to
`finding` / `workpaper` / `journal_entry` / `transaction` via `linked_entity_type` +
`linked_entity_id`) already exist and are more capable than what was originally proposed.
No new table is needed. Just add `organization_id` to `evidence_links` if it's missing
(see Priority 0.2).

### 1.2 Wire the existing tables into the pipeline as a blocking gate

**Fix — in `backend/app/services/risk_scoring.py`:**

```python
def run_risk_for_finding(finding_id):
    evidence_count = (
        db.query(EvidenceLink)
        .filter_by(finding_id=finding_id)
        .count()
    )
    if evidence_count == 0:
        raise EvidenceGateViolation(
            f"Finding {finding_id} has no linked evidence; cannot score risk."
        )
    # ... proceed to scoring
```

This check must be in the shared risk-scoring code path used by all three modules,
not duplicated per module — per the Generic Module Framework, this is a platform
engine concern. Confirm with Cursor first whether `risk_scoring.py` is already the
single shared entry point for all three modules, or whether each module still has
its own risk-scoring call site that needs the same check added individually.

**Acceptance:** a test that attempts to call risk scoring on a finding with zero
`evidence_links` rows raises `EvidenceGateViolation` and does not produce a risk score,
in all three modules.

### 1.3 Retrofit the three shipped modules

Run a backfill that creates `evidence_links` rows for every existing finding in Journal,
Revenue, and Procurement, using the finding's existing `journal_entry_ids` (rename
pending, see Priority 3.1) link — this is a one-time data migration, not new logic,
since the finding-to-source-row link already exists.

**Acceptance:** `SELECT count(*) FROM audit_findings f LEFT JOIN evidence_links e ON e.finding_id = f.id WHERE e.id IS NULL` returns 0.

### 1.4 Follow-up — auto-create `evidence_links` at finding generation (Part A)

**Gap found after M2:** the evidence gate correctly blocks risk scoring when findings
lack `evidence_links`, but the UI / legacy path runs **risk before generate-findings**.
On a first Run Analysis there are no findings yet (gate is a no-op); `generate_findings`
then created bare findings. A second Run Analysis hit `EvidenceGateViolation`.

**Fix (Part A — done):** `generate_findings`, `generate_revenue_findings`, and
`generate_procurement_findings` create placeholder `evidence` + `evidence_links` in the
**same transaction** as each new finding (same source-record relationship as migration
026). No finding can exist without evidence after commit.

### 1.5 Known debt — pipeline order vs Constitution (Part B deferred)

**Not a bug once Part A is in place.** The Product Constitution states the conceptual
order Rule → Evidence → Risk. Both the legacy UI sequence and `AnalysisEngine` still
run risk scoring **before** finding-generation:

- UI / legacy: upload → run-rules → **run-risk** → generate-findings
- `AnalysisEngine`: validation → rules → **risk** → findings → …

This no longer causes a functional failure (every finding has evidence at creation, so
a re-run’s risk step sees linked evidence). Reordering to literally match the Constitution
(Rule → Evidence/Findings → Risk) is **low-priority technical debt**, not a defect.
Do not treat this as a P0/P1 remediation item.

---

## Priority 2 — Auditor Decision Clarity

### 2.1 Reconcile the status vocabulary between code and constitution

**Problem:** the constitution describes Auditor Review actions as Accept / Reject / Mark
False Positive. The actual implementation's `FINDING_STATUSES` are: `open`,
`under_review`, `cleared`, `accepted`, `closed` — with `cleared` doing the job of both
"reject" and "false positive."

**Fix:** update the Constitution (not the code) to state the real vocabulary:
> Auditor Review actions are: move to Under Review, Clear (covers both rejection and
> false-positive), Accept, and Close. There is no separate false-positive status;
> `cleared` serves that purpose.

This is a documentation fix, not a code change — the lifecycle itself
(`open → under_review → cleared|accepted|closed`, with `closed → open` reopening) is sound.

### 2.2 Confirm reviewer identity is captured

**Problem:** no `reviewed_by` / `reviewed_at` field was mentioned alongside `status`.
Without it, the Final Report's required "Auditor Decision" field (§6.10) has no record
of *which* auditor made the decision or *when*.

**Fix (if not already present):**
```sql
ALTER TABLE audit_findings ADD COLUMN reviewed_by UUID;
ALTER TABLE audit_findings ADD COLUMN reviewed_at TIMESTAMPTZ;
```
Set both whenever `status` transitions away from `open` or `under_review`.

**Acceptance:** every finding with a `status` other than `open` has a non-null
`reviewed_by` and `reviewed_at`.

---

## Priority 3 — Cleanup (push past 95; do before Wave 3 modules)

### 3.1 Rename the shared finding-linkage field
`audit_findings.journal_entry_ids` → `audit_findings.source_record_ids`, since it already
holds invoice IDs for Revenue and Procurement findings. Naming it after one module while
three modules use it is Generic Module Framework debt that gets worse with every new module.

### 3.2 Add rule versioning
`rules_master` has no `version` column, but the Constitution's Rule Standard (§6.4) requires
one, and every finding should be traceable to the exact rule version that generated it, since
audit methodology changes over time.
```sql
ALTER TABLE rules_master ADD COLUMN version INT NOT NULL DEFAULT 1;
ALTER TABLE audit_findings ADD COLUMN rule_version INT;
```

### 3.3 Module catalog — no cleanup needed (retracted)
**The original 3.3 told you to delete 3 catalog entries. Don't.** ADR-002 and
`docs/business/03_MODULE_CATALOG.md` already settled that Compliance Checklist
Verification, Supporting Document Matching, and Exception Report Preparation are real
standalone catalog modules (#19–21), same as the other 19. That was the founder's
explicit, confirmed decision — the catalog is correct as-is. The only genuinely open
item in the catalog is #22 "Invoice Checking," whose exact scope has never been
disambiguated from Revenue Testing — that needs a product decision and a new ADR if
resolved, not a code change.

---

## Priority 4 — Infrastructure debt (operational risk, not a score blocker)

These don't block the 95+ score for design/architecture soundness, but they're real
production risk and should not be forgotten:

- **Object storage migration** off local disk (Constitution §7.7) — data-loss risk on redeploy.
- **Managed auth provider migration** (Constitution §7.3) — before any compliance work (Ch.8).
- **Legacy API consolidation** — three module-specific endpoint families
  (`/upload`, `/revenue/upload`, `/procurement/upload`) plus the generic
  `/modules/{code}/upload` means four code paths doing the same job. ADR-005 already
  plans deprecation headers and a 2-release-cycle sunset for these — confirm that
  sunset is actually scheduled, not just headers added and forgotten, before module four.

  **Proposed sunset condition (Remediation M5 Part A — awaiting confirmation; not locked):**
  Legacy mutation routes may be removed only when **both** gates are true
  (**whichever comes last**, not first):
  1. Advertised `Sunset` date **2026-12-31** has passed, **and**
  2. No production caller (frontend or otherwise) still depends on legacy paths —
     Wave 1 + Wave 2 modules and shipped-module clients use only `/modules/{code}/*`.
  Do **not** remove legacy routes on the date alone if Wave 1/2 (or any production
  client) still depends on them. See also `docs/status/CHANGELOG.md` [Unreleased]
  proposal note.

---

## Scoring checkpoint

| After completing | Expected score |
|---|---|
| Priority 0 only | ~85 |
| Priority 0 + 1 | ~92 |
| Priority 0 + 1 + 2 | ~95 |
| Priority 0–3 | 95+, and safe to resume building Wave 1 modules |

## Final acceptance checklist before declaring this remediation done

- [ ] Zero nullable `organization_id` anywhere in the tenant data chain
- [ ] Multi-tenant isolation test matrix passing for every table and module (RLS itself stays a Phase 3 item per ADR-003 — not part of this checklist)
- [ ] Zero findings without at least one `evidence_links` row, in all 3 modules
- [ ] Risk scoring raises an error on any finding with zero evidence — tested, not assumed
- [ ] Every non-`open`/`under_review` finding has `reviewed_by` and `reviewed_at`
- [ ] Constitution's Auditor Review section matches the real status vocabulary
- [ ] `source_record_ids` renamed, `rules_master.version` added, module catalog cleaned up
