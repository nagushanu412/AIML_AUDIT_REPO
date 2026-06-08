# AIML Audit Analytics — Backend

FastAPI backend foundation with PostgreSQL and Alembic migrations.

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

## Health checks

- `GET http://localhost:8000/health` — API status
- `GET http://localhost:8000/health/db` — Database connection + table verification

## Upload journal entries

`POST http://localhost:8000/upload` — multipart form with `file` (.xlsx)

Required columns: `Journal_ID`, `Posting_Date`, `Account_Code`, `Account_Name`, `Amount`, `Debit_Credit`, `User_ID`, `Description`

Optional query: `?project_id=<uuid>` (uses default project if omitted)

```bash
curl -X POST "http://localhost:8000/upload" -F "file=@../database/sample_journal_entries.xlsx"
```
