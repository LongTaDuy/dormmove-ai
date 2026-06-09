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

- **Backend**: FastAPI + Pydantic + SQLite (optional Redis checkpointing)
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

### 3. Docker (optional)

```bash
docker compose up --build
```

## Configuration

Copy `.env.example` to `.env` and adjust values. All variables have sensible
defaults so the app runs locally without external services or API keys.

## Status

This repository currently contains the project scaffold with minimal runnable
backend and frontend apps. See the roadmap below for next steps.

## Roadmap

- [x] Project structure + minimal runnable backend/frontend
- [ ] Pydantic domain models (student profile, plan, risks)
- [ ] Seed data (dorm items, dorm rules, products, categories)
- [ ] ModelRouter with mock model
- [ ] Rule-based agents + orchestrator
- [ ] Scoring engine
- [ ] Persistent sessions (SQLite) + optional Redis checkpointing
- [ ] Frontend intake form + plan view
- [ ] LangGraph integration behind the orchestrator interface
