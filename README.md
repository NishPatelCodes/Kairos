# Kairos

Personal AI executive assistant. Not a todo list.

The product loop:

```text
conversation → intent → validated tool call → schedule/goals update → better next recommendation
```

## Architecture

```text
frontend (React / Vite / Tailwind)
        │  JWT + JSON / SSE
        ▼
backend (Django / DRF)
        ├── accounts, goals, schedule, conversations, progress
        ├── schedule engine (deterministic time, conflicts, moves)
        ├── recommendation engine (scored next actions)
        └── AI orchestrator
                └── AIProvider
                      └── MistralProvider   (OpenAI later)
```

The LLM never writes to the database. It can only request tools. The backend validates ownership, times, and overlaps, then executes.

### Database (MVP)

- User, UserProfile, UserPreference
- AnnualGoal, MonthlyGoal
- ScheduleItem
- Conversation, Message

### Core API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register/` `/login/` `/refresh/` | Auth |
| GET/PATCH | `/api/auth/me/` | Profile + preferences |
| GET/POST | `/api/goals/annual/` `/monthly/` | Goals |
| GET/POST | `/api/schedule/` | Today's timeline |
| POST | `/api/ai/startup/` | Daily / onboarding opener |
| POST | `/api/ai/chat/` | SSE chat + tools |
| GET | `/api/progress/dashboard/` | Daily / weekly / monthly |

## Run locally

1. Copy `.env.example` to `.env` and set `MISTRAL_API_KEY`.
2. Leave `DATABASE_URL` empty to use SQLite, or start Postgres:

```bash
docker compose up db -d
```

3. Backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

4. Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

Optional demo data:

```bash
python manage.py seed_demo
```

Login: `demo@kairos.app` / `demo12345`

## Docker

```bash
docker compose up --build
```

Frontend still runs with `npm run dev` unless you add a frontend service.

## Deploy

Frontend goes to **Vercel**. Backend + Postgres go to **Render** (a persistent Django process, which SSE chat needs).

### 1. Push the repo to GitHub

```bash
git add .
git commit -m "Prepare Kairos for Vercel and Render"
git remote add origin https://github.com/YOUR_USER/kairos.git
git push -u origin master
```

### 2. Backend on Render

1. Open [https://dashboard.render.com](https://dashboard.render.com) and sign in with GitHub.
2. **New → Blueprint** and select this repo (`render.yaml` is already in the root).
3. Set these env vars on `kairos-api`:
   - `MISTRAL_API_KEY` — your Mistral key
   - `DJANGO_CORS_ORIGINS` — your Vercel origin, e.g. `https://kairos.vercel.app` (preview URLs on `*.vercel.app` are already allowed)
4. Deploy. Copy the API URL, e.g. `https://kairos-api.onrender.com`.
5. Confirm [https://kairos-api.onrender.com/api/health/](https://kairos-api.onrender.com/api/health/) returns `{"ok": true}`.

### 3. Frontend on Vercel

1. Open [https://vercel.com/new](https://vercel.com/new) and import the same GitHub repo.
2. Framework: Vite. Root directory can stay the repo root (`vercel.json` already points at `frontend/`).
3. Add environment variable:
   - `VITE_API_URL` = `https://kairos-api.onrender.com` (no trailing slash)
4. Deploy.

Or from the CLI after `vercel login`:

```bash
vercel --prod --cwd . -e VITE_API_URL=https://kairos-api.onrender.com
```

Chat streaming talks to Render directly. Do not proxy `/api` through Vercel.

## Notes

- All Mistral calls happen server-side. The API key never ships to the browser.
- Habits, weekly reviews, calendar sync, and notifications are intentionally Phase 2+.
