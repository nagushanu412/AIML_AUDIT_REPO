# AIML Audit Analytics — Backend

FastAPI backend with PostgreSQL, JWT auth, and the full audit hierarchy:

**Auditor → Clients → Engagements → Projects → Upload → Rules → Risk → Findings → Reports**

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # Edit POSTGRES_PASSWORD
```

## Run migrations

```bash
alembic upgrade head
```

## Start API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup the API seeds demo data:
- **User:** `auditor@demo.auditai.com` / `AuditAI2026!`
- **Client:** ABC Manufacturing (3 FY engagements, 9 projects)

Swagger UI: `http://localhost:8000/docs`

## Authentication

Public endpoints: `/health`, `/health/db`, `/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/forgot-password`, `/auth/logout`.

All other endpoints require `Authorization: Bearer <access_token>` and an **auditor portal role** (`auditor`, `partner`, `manager`, `admin`).

| Endpoint | Description |
|---|---|
| `POST /auth/register` | Create auditor account (bcrypt password hash) |
| `POST /auth/login` | Issue access + refresh tokens |
| `POST /auth/refresh` | Rotate refresh token, get new access token |
| `POST /auth/logout` | Revoke refresh token |
| `POST /auth/forgot-password` | Placeholder — always returns success message |
| `GET /auth/me` | Current user profile |

```powershell
@'
{"email":"auditor@demo.auditai.com","password":"AuditAI2026!"}
'@ | Set-Content -Encoding utf8 login.json

curl.exe -s -X POST "http://localhost:8000/auth/login" -H "Content-Type: application/json" -d "@login.json"
```

Access tokens expire in 60 minutes (configurable). Refresh tokens last 7 days and are stored hashed in `refresh_tokens`.

## Hierarchy APIs

| Endpoint | Description |
|---|---|
| `GET/POST /clients` | List / create clients |
| `GET/PATCH/DELETE /clients/{id}` | Client detail |
| `GET/POST /engagements?client_id=` | Engagements |
| `GET/POST /projects?engagement_id=` | Audit projects |
| `GET /rules` | Active rules from `rules_master` |

## Journal entry workflow

### 1. Upload (requires `project_id`)

```powershell
$token = "<access_token>"
$projectId = "<journal_testing_project_uuid>"
curl.exe -X POST "http://localhost:8000/upload?project_id=$projectId" `
  -H "Authorization: Bearer $token" `
  -F "file=@..\database\sample_journal_entries.xlsx"
```

Required columns: `Journal_ID`, `Posting_Date`, `Account_Code`, `Account_Name`, `Amount`, `Debit_Credit`, `User_ID`, `Description`

Response includes `total_debit` and `total_credit` in validation.

### 2. Run rules

```powershell
curl.exe -X POST "http://localhost:8000/run-rules?project_id=$projectId" -H "Authorization: Bearer $token"
```

### 3. Risk scoring

```powershell
curl.exe -X POST "http://localhost:8000/run-risk?project_id=$projectId" -H "Authorization: Bearer $token"
curl.exe "http://localhost:8000/risk-scores?project_id=$projectId" -H "Authorization: Bearer $token"
```

### 4. Findings & reports

```powershell
curl.exe -X POST "http://localhost:8000/generate-findings?project_id=$projectId" -H "Authorization: Bearer $token"
curl.exe "http://localhost:8000/findings?project_id=$projectId" -H "Authorization: Bearer $token"
curl.exe -X POST "http://localhost:8000/reports/generate?project_id=$projectId&report_type=journal_audit_summary" -H "Authorization: Bearer $token"
curl.exe "http://localhost:8000/reports" -H "Authorization: Bearer $token"
```

### 5. Dashboard

```powershell
curl.exe "http://localhost:8000/dashboard/summary" -H "Authorization: Bearer $token"
```

## Health checks

- `GET /health` — API status
- `GET /health/db` — Database connection

## Tests

```bash
pytest tests/ -v
```

## Frontend

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local` (optional; defaults to localhost:8000).

Login at `http://localhost:3000` with demo credentials, then use Journal Entry Testing under AI Audit Modules.
