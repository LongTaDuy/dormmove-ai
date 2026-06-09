# DormMove AI

An agentic move-in planning assistant for college students. DormMove AI collects a
student's dorm constraints, budget, school rules, already-owned items, roommate
situation, and move-in date, then generates a personalized, explainable move-in plan.

## What it generates

1. A personalized dorm checklist
2. A budget-aware shopping plan
3. Category-level product recommendations
4. A move-in timeline
5. Risk flags (overspending, duplicate items, prohibited dorm items, missing
   essentials, late shipping)

## Architecture

DormMove AI follows a multi-agent AI app pattern:

- **Backend**: FastAPI + Pydantic + SQLite session memory (optional Redis checkpointing)
- **Orchestrator**: LangGraph-style agent workflow. A mock/rule-based mode works
  out of the box; LangGraph can be plugged in later without changing the API.
- **Agents**: focused agents (intake, checklist, budget, recommendations,
  timeline, risk) coordinated by the orchestrator.
- **Scoring engine**: deterministic, explainable scoring for recommendations and
  risk flags.
- **ModelRouter**: an LLM abstraction. Defaults to a mock model so the app runs
  without paid API keys; OpenAI / Gemini / Bedrock can be added behind the same
  interface.
- **Frontend**: Next.js + TypeScript + TailwindCSS.

```
dormmove-ai/
  backend/        FastAPI service, agents, orchestrator, services, memory, data
  frontend/       Next.js app
  docker-compose.yml
  .env.example
```

## Quickstart

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env   # or copy .env.example manually on Windows
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the interactive API docs and
http://localhost:8000/health for a health check.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

The frontend reads the backend URL from `NEXT_PUBLIC_API_BASE_URL`
(defaults to `http://localhost:8000`).

Frontend pages:

| Route | Purpose |
|-------|---------|
| `/` | Landing page with value props and CTA |
| `/planner` | Chat-based move-in planner (creates/persists session) |
| `/results/[sessionId]` | Score breakdown and verdict |
| `/checklist/[sessionId]` | Filterable checklist by category |
| `/products/[sessionId]` | Product recommendations by category |
| `/timeline/[sessionId]` | Move-in timeline grouped by phase |

### 3. Docker (optional)

```bash
docker compose up --build
```

## Configuration

Copy `.env.example` to `.env` and adjust values. All variables have sensible
defaults so the app runs locally without external services or API keys.

### Session persistence (SQLite)

Chat sessions, messages, and plan snapshots are persisted in a local SQLite
database so they survive restarts. The database location is controlled by the
`DORMMOVE_SQLITE_PATH` environment variable and defaults to
`backend/local_data/dormmove.sqlite3` (created automatically on first run).
The `local_data/` folder and `*.sqlite3` / `*.db` files are gitignored.

### Model router (mock vs OpenAI)

LLM support is **optional** and **off by default**. Mock mode runs the same
deterministic parsers and agents with no API key.

**Mock mode (default):**

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:DORMMOVE_MODEL_PROVIDER="mock"
uvicorn app.main:app --reload --port 8000
```

**OpenAI mode** (profile extraction + intent classification only):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:OPENAI_API_KEY="your-key-here"
$env:DORMMOVE_MODEL_PROVIDER="openai"
$env:DORMMOVE_LLM_MODEL="gpt-4o-mini"
uvicorn app.main:app --reload --port 8000
```

What the LLM does:

- **Profile extraction** — supplements the deterministic parser when fields are
  hard to parse (e.g. `28th aug 2026`, compact follow-up messages).
- **Intent classification** — optional high-confidence routing in ConciergeAgent.

What stays **deterministic** (never LLM-controlled):

- Checklist generation
- Dorm rules audit
- Budget allocation
- Product recommendations
- Move-in timeline
- MoveInScoringEngine / final verdict

**Fallback behavior:** If OpenAI times out or errors and
`DORMMOVE_ALLOW_LLM_FALLBACK=true` (default), ModelRouter returns mock-style
deterministic output with `fallback_used=true` so the app keeps working.
Session caps (`DORMMOVE_MAX_MODEL_CALLS_PER_SESSION`,
`DORMMOVE_MAX_ESTIMATED_COST_PER_SESSION_USD`) block further model calls per
session when exceeded.

Never commit `.env` or API keys. Use `.env.example` placeholders only.

### API routes

| Method | Route | Purpose |
|--------|-------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/sessions` | Create a session (optional `title` in body) |
| `GET` | `/api/v1/sessions` | List sessions with score, verdict, message count |
| `GET` | `/api/v1/sessions/{id}` | Full session snapshot (profile, messages, plan) |
| `GET` | `/api/v1/sessions/{id}/plan` | Latest move-in plan |
| `GET` | `/api/v1/sessions/{id}/checklist` | Checklist with status summary |
| `GET` | `/api/v1/sessions/{id}/products` | Product recommendations by category |
| `GET` | `/api/v1/sessions/{id}/timeline` | Move-in timeline with phase summary |
| `GET` | `/api/v1/metrics/runtime` | Aggregate runtime metrics from SQLite |
| `POST` | `/api/v1/chat` | Chat within a session; persists profile and plan |

## Status

This repository currently contains the project scaffold with minimal runnable
backend and frontend apps. See the roadmap below for next steps.

## Roadmap

- [x] Project structure + minimal runnable backend/frontend
- [x] Pydantic domain models (student profile, plan, risks)
- [x] Seed data (dorm items, dorm rules, products, categories)
- [x] ModelRouter with mock model (+ optional OpenAI)
- [x] Rule-based agents + orchestrator
- [x] Scoring engine
- [x] Persistent sessions (SQLite) + optional Redis checkpointing
- [x] Frontend-ready API routes (checklist, products, timeline, metrics)
- [x] Frontend planner + plan views (checklist, products, timeline, results)
- [ ] LangGraph integration behind the orchestrator interface
