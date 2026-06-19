# AIML Audit — Production Deployment Guide

Deploy **Frontend → Vercel** | **Backend + PostgreSQL → Railway**

---

## Architecture

```
Browser → Vercel (Next.js 14)
              ↓ NEXT_PUBLIC_API_URL
         Railway (FastAPI + uvicorn)
              ↓ DATABASE_URL
         Railway PostgreSQL
```

---

## Changes made for production

| Area | Change |
|---|---|
| `backend/app/config.py` | `PORT` / `API_PORT`, `DATABASE_URL` normalization (`postgres://` → `postgresql://`), `CORS_ORIGIN_REGEX`, `ENVIRONMENT`, `MAX_UPLOAD_MB` |
| `backend/app/main.py` | CORS regex for Vercel previews; JWT default-secret warning in production |
| `backend/app/routers/upload.py` | Max upload size limit (10 MB default) |
| `backend/start.sh` | Reads `$PORT` for Railway |
| `backend/Dockerfile` | Production container build |
| `backend/railway.toml` | Start + release (migrations) commands |
| `backend/Procfile` | Heroku/Railway compatibility |
| `.env.example` | Frontend variables |
| `backend/.env.example` | All backend variables |
| `next.config.mjs` | Security headers |
| `lib/api/config.ts` | Strips trailing slash from API URL |

---

## Prerequisites

- GitHub repo pushed (`architecture` branch)
- [Railway](https://railway.app) account
- [Vercel](https://vercel.com) account
- OpenSSL or similar to generate JWT secret:
  ```bash
  openssl rand -hex 32
  ```

---

## Part 1 — Deploy Backend to Railway

### Step 1: Create Railway project

1. Go to [railway.app](https://railway.app) → **New Project**
2. **Deploy from GitHub repo** → select `AIML_AUDIT_REPO`
3. Choose branch: **`architecture`**

### Step 2: Set root directory to `backend`

1. Open the backend **service** → **Settings**
2. **Root Directory:** `backend`
3. Save — Railway will use `backend/railway.toml` and `backend/Dockerfile`

### Step 3: Add PostgreSQL

1. In the same project → **+ New** → **Database** → **PostgreSQL**
2. Railway injects `DATABASE_URL` into linked services automatically
3. **Variables** → **Add Reference** → link `DATABASE_URL` from Postgres to your API service

### Step 4: Configure environment variables (Railway API service)

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (reference from PostgreSQL plugin) |
| `JWT_SECRET_KEY` | Your `openssl rand -hex 32` value |
| `CORS_ORIGINS` | `https://YOUR-APP.vercel.app` (update after Vercel deploy) |
| `CORS_ORIGIN_REGEX` | `https://.*\.vercel\.app` (optional — Vercel previews) |
| `DEMO_USER_EMAIL` | `auditor@demo.auditai.com` |
| `DEMO_USER_PASSWORD` | `AuditAI2026!` |
| `MAX_UPLOAD_MB` | `10` |

**Do not set** `PORT` — Railway sets it automatically.

### Step 5: Migrations (automatic)

`railway.toml` runs on each deploy:

```
releaseCommand = "alembic upgrade head"
```

Manual run (if needed) → Railway service → **Shell**:

```bash
alembic upgrade head
```

### Step 6: Deploy and get backend URL

1. **Deploy** the service
2. **Settings** → **Networking** → **Generate Domain**
3. Copy URL, e.g. `https://aiml-audit-api-production.up.railway.app`

### Step 7: Verify backend

```bash
curl https://YOUR-BACKEND.up.railway.app/health
```

Expected:

```json
{"status":"ok","service":"AIML Audit Analytics API"}
```

```bash
curl https://YOUR-BACKEND.up.railway.app/health/db
```

Expected: `"migrations_applied": true`

---

## Part 2 — Deploy Frontend to Vercel

### Step 1: Import project

1. [vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import `AIML_AUDIT_REPO` from GitHub
3. Branch: **`architecture`**

### Step 2: Framework settings

| Setting | Value |
|---|---|
| Framework Preset | Next.js |
| Root Directory | `.` (repo root) |
| Build Command | `npm run build` (default) |
| Output Directory | `.next` (default) |

### Step 3: Environment variables (Vercel)

| Variable | Value | Environments |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-BACKEND.up.railway.app` | Production, Preview, Development |

**No trailing slash** on the API URL.

### Step 4: Deploy

Click **Deploy**. Copy your Vercel URL, e.g. `https://aiml-audit.vercel.app`

### Step 5: Update Railway CORS

Back in Railway → API service → **Variables**:

```
CORS_ORIGINS=https://aiml-audit.vercel.app,http://localhost:3000
```

Redeploy backend after updating CORS.

---

## Part 3 — Connect Frontend to Backend

| Check | How |
|---|---|
| API URL | Vercel env `NEXT_PUBLIC_API_URL` = Railway public URL |
| CORS | Railway `CORS_ORIGINS` includes Vercel URL |
| HTTPS | Both Vercel and Railway use HTTPS by default |
| Auth | JWT tokens work cross-origin (Bearer header) |

---

## Production verification checklist

Run on **production Vercel URL** with demo login:

| # | Test | Pass |
|---|---|---|
| 1 | Login (`auditor@demo.auditai.com` / `AuditAI2026!`) | ☐ |
| 2 | Register (optional new user) | ☐ |
| 3 | Dashboard loads | ☐ |
| 4 | Clients list (ABC Manufacturing) | ☐ |
| 5 | Engagements list | ☐ |
| 6 | Projects list | ☐ |
| 7 | Journal Entry Testing — select hierarchy | ☐ |
| 8 | Upload Excel (`sample_journal_entries.xlsx`) | ☐ |
| 9 | Run AI Analysis | ☐ |
| 10 | Risk scores + findings display | ☐ |
| 11 | Export Excel report | ☐ |
| 12 | Export PDF report | ☐ |
| 13 | Export working paper | ☐ |
| 14 | Reports page + download | ☐ |
| 15 | Documents page + download | ☐ |
| 16 | Audit Rules (view + edit) | ☐ |
| 17 | Dashboard charts after analysis | ☐ |
| 18 | Logout + re-login | ☐ |

---

## Security recommendations

| Item | Status | Action |
|---|---|---|
| JWT secret | Required | Set strong `JWT_SECRET_KEY` in Railway |
| Password hashing | OK | bcrypt via passlib |
| CORS | Configured | Restrict to your Vercel domain in production |
| HTTPS | OK | Vercel + Railway default |
| Security headers | Added | `next.config.mjs` (X-Frame-Options, etc.) |
| File upload | Limited | `.xlsx` only, 10 MB max |
| API validation | OK | Pydantic schemas on all endpoints |
| Demo password | Change | Use strong `DEMO_USER_PASSWORD` for CA demo |
| Report files | Ephemeral | `generated_reports/` on Railway disk — re-export after redeploy |

### Optional hardening (future)

- Next.js API proxy for httpOnly cookies
- Rate limiting on `/auth/login`
- Rotate JWT secrets periodically
- Remove demo seed in production (`ENVIRONMENT=production` + disable seed)

---

## Local development (unchanged)

**Backend:**

```bash
cd backend
copy .env.example .env
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
copy .env.example .env.local
npm install
npm run dev
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| CORS error in browser | Add Vercel URL to Railway `CORS_ORIGINS`; redeploy backend |
| `Failed to fetch` on login | Check `NEXT_PUBLIC_API_URL`; verify `/health` responds |
| Database connection failed | Confirm `DATABASE_URL` reference from PostgreSQL plugin |
| `relation does not exist` | Run `alembic upgrade head` in Railway shell |
| Upload fails 413 | File > 10 MB — increase `MAX_UPLOAD_MB` or use smaller file |
| Reports missing after redeploy | Railway ephemeral disk — re-run analysis and export |
| JWT errors after deploy | Ensure same `JWT_SECRET_KEY` across redeploys |

---

## Quick reference — environment variables

### Railway (backend)

```
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
JWT_SECRET_KEY=<openssl rand -hex 32>
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
DEMO_USER_EMAIL=auditor@demo.auditai.com
DEMO_USER_PASSWORD=AuditAI2026!
MAX_UPLOAD_MB=10
```

### Vercel (frontend)

```
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
```

---

## Deployment order (summary)

1. Deploy **Railway PostgreSQL**
2. Deploy **Railway backend** (`backend/` root) + env vars
3. Verify `/health` and `/health/db`
4. Deploy **Vercel frontend** with `NEXT_PUBLIC_API_URL`
5. Update Railway **CORS_ORIGINS** with Vercel URL
6. Redeploy backend
7. Run **verification checklist**

---

*AIML Audit — architecture branch — Vercel + Railway deployment*
