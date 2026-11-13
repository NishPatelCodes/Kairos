<p align="center">
  <img src="logo.png" alt="Kairos logo" width="96" />
</p>

<h1 align="center">Kairos</h1>

<p align="center">
  A personal AI executive assistant that plans your day around your goals.<br />
  You talk to it. It manages the schedule.
</p>

---

## What it does

Kairos is a chat-first planner, not a todo list. You tell it what you want to get done, and it turns the conversation into a real schedule tied to your monthly and annual goals.

```text
conversation → intent → validated tool call → schedule / goals update → better next recommendation
```

- **Today**: a chat panel beside a live timeline of your day, with resizable panes.
- **Goals**: annual goals broken into monthly goals, each with trackable progress.
- **Progress**: daily, weekly and monthly dashboards.
- **Settings**: working hours and preferences the assistant plans around.

## How it works

```text
frontend (React / Vite / Tailwind)
        │  JWT + JSON / SSE
        ▼
backend (Django / DRF)
        ├── accounts, goals, schedule, conversations, progress
        ├── schedule engine        deterministic time, conflicts, moves
        ├── recommendation engine  scored next actions
        └── AI orchestrator
                └── AIProvider
                      └── MistralProvider
```

**The model never writes to the database.** It can only request tools. The backend checks ownership, times and overlaps, and then runs the change itself.

The assistant can call these tools:

| Area | Tools |
| --- | --- |
| Read | `get_today_schedule`, `get_free_slots`, `get_monthly_goals`, `get_annual_goal`, `get_recent_activity`, `get_productivity_insights` |
| Schedule | `create_schedule_item`, `update_schedule_item`, `move_schedule_item`, `delete_schedule_item`, `complete_task`, `apply_day_plan` |
| Goals | `create_goal`, `update_goal`, `increment_goal_progress` |
| Profile | `update_preferences` |

## Tech stack

| Layer | Stack |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, Radix UI, TanStack Query, Recharts, Framer Motion |
| Backend | Python 3.12, Django 5, Django REST Framework, SimpleJWT |
| AI | Mistral (server-side only, behind a swappable `AIProvider` interface) |
| Database | SQLite for local development, PostgreSQL in production |
| Hosting | Vercel (frontend), Render (API and Postgres) |

## Project structure

```text
backend/
  apps/
    accounts/        users, profiles, preferences, auth
    goals/           annual and monthly goals
    schedule/        schedule items and the scheduling engine
    conversations/   chat history
    progress/        daily / weekly / monthly stats
    ai/              orchestrator, prompts, provider, tools
  config/            Django settings and URLs
frontend/
  src/
    pages/           Today, Goals, Progress, Settings, Auth
    components/      chat, schedule, goals, layout, ui
    lib/             API client
render.yaml          Render blueprint (API + Postgres)
vercel.json          Vercel build config
docker-compose.yml   local Postgres + backend
```

## Run locally

You need Python 3.12+, Node 20+, and a [Mistral API key](https://console.mistral.ai/).

**1. Environment**

Copy `.env.example` to `.env` and fill in your own values:

```bash
cp .env.example .env
```

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Any long random string |
| `DJANGO_DEBUG` | `true` locally, `false` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts |
| `DJANGO_CORS_ORIGINS` | Frontend origin, e.g. `http://localhost:5173` |
| `DATABASE_URL` | Leave empty to use SQLite |
| `MISTRAL_API_KEY` | Your Mistral key |
| `MISTRAL_MODEL` | Defaults to `mistral-small-latest` |
| `VITE_API_URL` | Leave empty locally; the API origin in production |

**2. Backend**

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**3. Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

**Optional: demo data**

```bash
python manage.py seed_demo
```

This creates a local-only demo account: `demo@kairos.app` / `demo12345`. Do not run it against a production database.

**Optional: Postgres with Docker**

```bash
docker compose up --build
```

This starts Postgres and the backend. The frontend still runs with `npm run dev`.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register/`, `/login/`, `/refresh/` | Auth (JWT) |
| GET / PATCH | `/api/auth/me/` | Profile and preferences |
| GET / POST | `/api/goals/annual/`, `/api/goals/monthly/` | Goals |
| GET / POST | `/api/schedule/` | Today's timeline |
| POST | `/api/schedule/<id>/complete/`, `/move/` | Complete or move an item |
| GET | `/api/conversations/today/` | Today's conversation |
| POST | `/api/ai/startup/` | Daily or onboarding opener |
| POST | `/api/ai/chat/` | Streaming chat (SSE) with tools |
| GET | `/api/progress/daily/`, `/weekly/`, `/monthly/`, `/dashboard/` | Progress stats |
| GET | `/api/health/` | Health check |

## Deploy

The frontend goes to **Vercel**. The API and Postgres go to **Render**, because streaming chat needs a long-running Django process.

**Backend on Render**

1. In the [Render dashboard](https://dashboard.render.com), choose **New → Blueprint** and select this repo. `render.yaml` sets up the service and database.
2. Set these on the `kairos-api` service:
   - `MISTRAL_API_KEY`: your Mistral key
   - `DJANGO_CORS_ORIGINS`: your Vercel origin
3. Deploy, then check that `/api/health/` returns `{"ok": true}`.

**Frontend on Vercel**

1. Import the repo at [vercel.com/new](https://vercel.com/new). The root directory stays the repo root; `vercel.json` points at `frontend/`.
2. Add `VITE_API_URL` set to your Render API URL, with no trailing slash.
3. Deploy.

Chat streaming talks to Render directly. Do not proxy `/api` through Vercel.

## Security

- Secrets live in `.env` locally and in the Render / Vercel dashboards in production. `.env` is git-ignored; only `.env.example` with placeholder values is committed.
- All Mistral calls happen on the server. The API key never reaches the browser.
- Every tool call from the model is validated against the signed-in user before anything is written.

## Roadmap

Habits, weekly reviews, calendar sync and notifications are planned for a later phase.
