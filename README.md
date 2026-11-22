# Jev-Job

A personal job-application tracker. The backend syncs job-related emails from Gmail, has an LLM
label each one with a status, company and role, groups them into applications, and computes
every dashboard number. The React dashboard only displays what the API sends, behind a Google
login restricted to one account.

- `server/`: FastAPI + Beanie/MongoDB backend
- `app/`: Vite + React + TanStack Query dashboard

## What the dashboard shows

- **Overview**: KPIs, response funnel, status breakdown and short insights
- **Timeline**: applications per week by outcome, plus an activity heatmap
- **Patterns**: results by role, weekday and hour of day
- **Applications**: a filterable table and per-application process lanes
- **Companies**: a company grid and each company's history
- **Sync**: last sync time, email count and a "Sync now" button with live progress

Filters (search, company, role, status, date range) apply across the widgets.

## Configuration

Copy the example files and fill them in:

```sh
cp .env.example .env          # backend, read from the repo root
cp app/.env.example app/.env  # frontend
```

Backend (`.env`):

| Variable | Purpose |
|---|---|
| `PERSONAL_EMAIL`, `FIRSTNAME`, `LASTNAME`, `PHONE_NUMBER` | your details, redacted from emails before they go to the LLM |
| `GOOGLE_SUB` | Google account ID (`sub`) allowed to sign in; everyone else gets 403 |
| `ALLOWED_ORIGINS` | comma-separated browser origins allowed by CORS (default `http://localhost:5173`) |
| `OPENROUTER_DECISIONS_API_KEY`, `OPENROUTER_DECISIONS_BASE_URL` | decisions API used while classifying emails |
| `OPENROUTER_LLM_API_KEY`, `OPENROUTER_LLM_BASE_URL` | LLM used to label emails |
| `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` | Gmail API access for the sync |
| `AUTH_CLIENT_ID`, `AUTH_CLIENT_SECRET` | Google OAuth client for the dashboard login |
| `SESSION_SECRET_KEY` | signs the session cookie |
| `MONGO_CONNECTION_STRING` | MongoDB connection string |
| `ENVIRONMENT` | `dev` allows a non-HTTPS session cookie and redirects to `APP_DEV` after login |
| `APP_DEV`, `APP_PROD` | dashboard URL to return to after login, in dev and production |

Frontend (`app/.env`):

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | backend URL, e.g. `http://localhost:8000` |

## Running

### Docker Compose

```sh
docker compose up --build
```

The backend runs on http://localhost:8000 and the dashboard on http://localhost:5173, both with
hot reload. The backend reads `.env` from the repo root.

### Locally

Backend (Python 3.13 + [uv](https://docs.astral.sh/uv/)), from the repo root:

```sh
uv sync --project server
uv run --project server uvicorn server.app:app --reload
```

Frontend (Node 24):

```sh
cd app
npm install
npm run dev
```

Open http://localhost:5173, sign in with Google, and press "Sync now" to pull emails.

## Tests and checks

```sh
cd server && uv run pytest                     # backend tests
cd app && npm run build && npm run lint        # type check, build and oxlint
```
