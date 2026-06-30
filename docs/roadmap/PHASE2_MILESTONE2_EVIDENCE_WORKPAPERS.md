# Phase 2 Milestone 2 — Workpapers & Evidence Repository

**Status:** Complete  
**Migration:** `015_workpapers_evidence`  
**Date:** 2026-06-07

## Scope

Enterprise evidence repository and workpaper management with file upload, versioning, categories, metadata, search, and finding links.

## Database

| Table | Purpose |
|-------|---------|
| `evidence` | Evidence files with versioning |
| `workpapers` | Workpaper index with optional attachments |
| `evidence_links` | Link evidence to findings, workpapers, transactions |

## API Endpoints

### Evidence

| Method | Path |
|--------|------|
| GET | `/engagements/{id}/evidence` |
| POST | `/engagements/{id}/evidence` (multipart upload) |
| POST | `/engagements/{id}/evidence/{id}/versions` |
| GET | `/engagements/{id}/evidence/{id}/versions` |
| GET | `/engagements/{id}/evidence/{id}/download` |
| POST | `/engagements/{id}/evidence/{id}/links` |
| GET | `/engagements/{id}/evidence/{id}/links` |

### Workpapers

| Method | Path |
|--------|------|
| GET | `/engagements/{id}/workpapers` |
| POST | `/engagements/{id}/workpapers` |
| PATCH | `/engagements/{id}/workpapers/{id}` |
| POST | `/engagements/{id}/workpapers/{id}/upload` |
| GET | `/engagements/{id}/workpapers/{id}/versions` |
| GET | `/engagements/{id}/workpapers/{id}/download` |

## Storage

Local filesystem under `backend/storage/` (Milestone 6 adds S3/Azure/GCS adapters).

## Frontend

Engagements page → **Evidence** panel (evidence + workpapers tabs).

---

*Next milestone: Finding Lifecycle (Milestone 3)*
