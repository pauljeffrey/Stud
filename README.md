# Stud

**Master Medicine Through Adventure**

Stud is a gamified medical education platform that combines multi-agent AI orchestration, structured clinical state management, and immersive UI to turn healthcare learning into an interactive role-playing experience. It supports three learning modes—**Mediquest** (clinical adventures), **Study** (document-grounded chat), and **Quiz** (assessment)—behind a unified FastAPI backend and Next.js frontend.

**Creator:** Dr. Jeffrey Otoibhi

---

## Table of Contents

- [Overview](#overview)
- [Decision & Idea Choices](#decision--idea-choices)
- [Architectural Choices](#architectural-choices)
- [Engineering Bottlenecks](#engineering-bottlenecks)
- [Trade-offs](#trade-offs)
- [Evaluation](#evaluation)
- [Edge Cases](#edge-cases)
- [Academic Work](#academic-work)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Further Documentation](#further-documentation)

---

## Overview

Stud targets a gap between static medical content (PDFs, question banks) and passive AI chatbots. The platform treats clinical learning as a **stateful game**: worlds are generated, cases evolve based on performance, NPCs provide in-character guidance, and outcomes feed achievements and progression metrics.

| Mode | Purpose | Core mechanism |
|------|---------|----------------|
| **Mediquest** | Immersive clinical scenarios | Multi-agent game loop (world → case → escalation → handoff) |
| **Study** | Document-based learning | RAG over uploaded files with streaming tutor chat |
| **Quiz** | Knowledge assessment | AI-generated MCQ + open-ended questions with LLM scoring |

---

## Decision & Idea Choices

### 1. Gamification over static content delivery

**Choice:** Frame medical education as a role-playing adventure with timers, clues, NPCs, achievements, and escalating cases—not as a linear quiz app.

**Rationale:** Clinical reasoning benefits from narrative context, time pressure, and iterative decision-making. A game loop encourages repeated practice with varied scenarios rather than one-shot memorization.

### 2. Multi-agent decomposition instead of a single mega-prompt

**Choice:** Split responsibilities across specialized agents rather than one monolithic LLM call for all game logic.

| Agent | Responsibility |
|-------|----------------|
| **Game World Agent** | Setting, hospital, era, resource constraints |
| **Game Master Agent** | Case generation, achievements, orchestration, player chat |
| **State Controller Agent** | Escalation/de-escalation based on answers and performance |
| **NPC Agent** | In-character dialogue tied to case context |
| **Quiz / Tutor agents** | Assessment and document-grounded tutoring |

**Rationale:** Separation improves prompt focus, allows independent model selection per agent, and mirrors how clinical teams divide roles (environment, case lead, bedside staff).

### 3. Structured state models (Pydantic) as the contract

**Choice:** Represent game progress in typed models (`GameState`, `CaseState`, `NPCState`, `GameWorldModel`, `PerformanceAnalysis`) with a shared `CommonFields` abstraction for repeated metadata.

**Rationale:** LLM outputs are validated and normalized before persistence. The API and frontend share a predictable schema instead of ad-hoc JSON blobs.

### 4. Bring-your-own-key (BYOK) with platform fallback

**Choice:** Users may supply their own model name and API key (encrypted at rest with Fernet); the backend falls back to system-configured models when user credentials are missing or invalid.

**Rationale:** Reduces platform LLM cost for power users, supports model preference, and keeps demo/onboarding functional without mandatory key setup.

### 5. Demo mode without full database coupling

**Choice:** Demo sessions use synthetic `demo_*` user IDs, Redis-backed session state, and skip Supabase persistence when IDs are not valid UUIDs.

**Rationale:** Lowers friction for first-time users and avoids polluting production user tables with anonymous trials.

### 6. BFF proxy pattern on the frontend

**Choice:** Next.js route handlers (`/api/*`) proxy to the Python backend via a shared `proxy()` helper, forwarding auth headers and SSE streams.

**Rationale:** Keeps secrets off the client, unifies CORS, and allows environment-specific backend URLs without exposing internal services.

### 7. Dual-layer game state on the client

**Choice:** The Mediquest UI maintains a **display-normalized** state for rendering and a **backend canonical** ref (`game_config`, `case_metadata`, full `game_world`, etc.) merged via `toBackendPayload()` before every API call.

**Rationale:** The UI only needs a subset of fields; sending stripped state caused backend validation failures. Canonical refs preserve server-only fields while allowing UI updates.

---

## Architectural Choices

### System topology

```
┌─────────────────┐     /api/* proxy      ┌──────────────────────────────┐
│  Next.js 16     │ ───────────────────►  │  FastAPI (python_backend)    │
│  React 18       │     SSE for chat      │  Pydantic-AI agents          │
│  Tailwind/Radix │                       │  game_v2 · quiz · learning   │
└─────────────────┘                       └──────────────┬───────────────┘
                                                         │
                    ┌────────────────────────────────────┼────────────────────────┐
                    ▼                    ▼                 ▼                        ▼
              Supabase (PG)          Redis           OpenRouter /              Pinecone /
              users, games,            sessions,       Gemini / OpenAI           pgvector
              quizzes, docs            hot cache       (via pydantic-ai)         (RAG)
```

### Backend layering

| Layer | Location | Role |
|-------|----------|------|
| **API routers** | `python_backend/api/` | HTTP contracts, auth deps, rate limits, SSE responses |
| **Agents** | `python_backend/agents/` | LLM orchestration, tool use, streaming generation |
| **Models** | `python_backend/models/` | Pydantic schemas for game, quiz, tutor flows |
| **Services** | `python_backend/service/` | Database, Redis, S3, crypto, document processing |
| **Config** | `python_backend/configs/` | Game settings enums, environment-driven model names |

Key API modules: `game_v2.py` (Mediquest), `quiz.py`, `learning.py`, `auth.py`, `user.py`.

### Mediquest runtime flow

1. **Initialize** — Game World Agent creates setting; Game Master generates first case; NPC Agent creates characters; state cached in Redis and optionally persisted to Supabase.
2. **Play** — User chats (Game Master / NPCs via SSE), uses clues, submits answers; State Controller updates case difficulty.
3. **Handoff** — When `n_changes >= max_clinical_changes`, Game Master evaluates performance, awards achievements, and generates the next case.
4. **Client sync** — `parse_client_game_state()` on the backend and `toBackendPayload()` on the frontend keep payloads valid across round-trips.

### Frontend architecture

- **App Router** (`frontend/app/`) with route-level pages for demo, mediquest, study, quiz, dashboard, auth.
- **Shared game helpers** (`frontend/app/lib/game-state.ts`, `proxy.ts`) centralize normalization, SSE parsing, and API error extraction.
- **Design system** — Radix UI primitives, Framer Motion animations, purple/navy clinical aesthetic.

### Authentication & security

- Custom JWT + bcrypt (not Supabase Auth); sessions stored in `user_sessions` with best-effort writes so auth never hard-fails on missing tables.
- API keys encrypted with **Fernet (AES-128-CBC + HMAC)** before Supabase storage; legacy plain-text values still decrypt.
- Rate limiting with **fail-open** wrapper so Redis outages do not block login.
- Production CORS enforced via `ALLOWED_ORIGINS` when `PRODUCTION=1`.

### Deployment

- **Backend:** Docker Compose (local, production, Dokploy/Traefik variants), Gunicorn + Uvicorn workers, live-mount dev reload.
- **Frontend:** Vercel-compatible Next.js build; `PYTHON_BACKEND_URL` points proxy at the API.

---

## Engineering Bottlenecks

### 1. External LLM latency and rate limits

The backend is **I/O-bound**: most request time waits on OpenRouter, Gemini, or OpenAI. Game initialization alone may invoke the Game World Agent, Game Master, State Controller, and NPC Agent in sequence—often **10–30+ seconds** on cold paths.

**Mitigations implemented:** OpenRouter prompt caching, dedicated init agents (tool-free paths to avoid extra LLM round-trips), character-chunk SSE streaming for perceived responsiveness, `select_model_with_fallback()` for resilient model selection.

### 2. Multi-step game initialization

Each new Mediquest session triggers world creation, case generation, and NPC batch generation. This is inherently expensive and difficult to parallelize fully because later steps depend on earlier outputs.

**Mitigations:** Redis session cache returns quickly after init; init payload cached in `sessionStorage` on the client to skip re-fetch; background DB persist so HTTP response is not blocked.

### 3. Frontend ↔ backend state schema drift

The UI normalizes field names (`examination_findings` vs `investigations`, top-level `npc_states` vs nested). Sending incomplete state caused 500 errors on clue, submit, and chat endpoints.

**Mitigations:** `game_state_utils.parse_client_game_state()`, `toBackendPayload()` with deep merge, `mergeBackendFromResponse()` to preserve nested objects after API responses.

### 4. Document processing spikes

Uploading and chunking PDFs/DOCX/PPT is **CPU- and memory-intensive** (100–300 MB per heavy request per internal capacity docs).

**Mitigations:** 2-hour expiry for free-tier documents, cleanup worker on startup, lazy tutor agent init so model errors do not crash the entire app.

### 5. Database write pressure for ephemeral users

Demo and malformed `user_id` values previously caused failed Supabase upserts that surfaced as user-visible 500 errors.

**Mitigations:** `_valid_uuid()` gate on persist; best-effort session/logout/delete; demo games live in Redis only.

### 6. Single-server concurrency ceiling

On a typical 8 GB / 2 vCPU node, realistic concurrent active users are on the order of **50–150** before AI provider limits or memory dominate (see `python_backend/about/capacity-and-scaling.md`).

---

## Trade-offs

| Decision | Benefit | Cost |
|----------|---------|------|
| **Multi-agent vs single agent** | Clear prompts, modular testing, per-agent models | Higher init latency, more moving parts |
| **Pydantic-strict game state** | Type safety, fewer silent data bugs | Client must send complete backend fields |
| **Redis cache** | Fast session reads, demo support | Optional dependency; cache/DB can diverge briefly |
| **BYOK** | User cost control, model choice | Encryption key management; support burden |
| **SSE streaming** | Responsive chat UX | Harder error handling; proxy must forward headers |
| **Concise generation prompts** | Faster tokens, cleaner UI | Less narrative richness per case |
| **Fail-open rate limits / session writes** | Auth works under partial outages | Weaker abuse protection when Redis/DB flaky |
| **Next.js proxy vs direct API calls** | Security, single origin | Extra hop; duplicate route files |

---

## Evaluation

### Functional coverage

| Area | Status | Notes |
|------|--------|-------|
| Mediquest init + play | Implemented | Multi-agent loop, clue/submit/chat, achievements |
| Quiz generation & scoring | Implemented | MCQ + open-ended with LLM analysis |
| Study / document chat | Implemented | Upload, RAG, streaming tutor |
| Auth & dashboard | Implemented | JWT, encrypted API keys, stats tabs |
| Demo mode | Implemented | Session-limited, Redis-first |

### Automated testing

Integration tests live in `tests/ai_tests/` and target a **running** backend (`BASE_URL`, default `http://localhost:8000`):

- Health and session ID contract tests
- Learning chat flow (requires `STUD_TEST_DOCUMENT_ID` for full path)
- Optional **LLM judge** when `OPENAI_API_KEY` / `JUDGE_API_KEY` is set

```bash
pip install -r tests/ai_tests/requirements-ai.txt
pytest tests/ai_tests -v
```

### Manual evaluation checklist

- [ ] Demo game: init → scenario popup → clue → submit → Game Master chat → NPC chat
- [ ] Registered user: login → dashboard stats → settings API key save/load
- [ ] Study: upload PDF → chat with citations → generate quiz
- [ ] Error toasts show backend `detail` messages (not generic failures)

### Performance expectations (indicative)

From internal capacity analysis (`python_backend/about/capacity-and-scaling.md`):

- Light API: tens of ms (excluding LLM)
- Agent call: 2–10 s per LLM round-trip
- Game init: often 15–45 s depending on model and provider
- Document upload/process: seconds to minutes by file size

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| **Demo `user_id` (`demo_*`)** | Skips Supabase game persist; Redis holds session |
| **Invalid / missing UUID on persist** | DB write skipped with warning log, request still succeeds |
| **Redis unavailable** | Cache miss → Supabase fallback; rate limit fail-open |
| **User API key invalid** | Falls back to system default model (`select_model_with_fallback`) |
| **Legacy plain-text API keys in DB** | Decrypt returns value as-is when Fernet prefix absent |
| **Client sends stripped `game_state`** | `parse_client_game_state()` maps UI fields; `toBackendPayload()` merges canonical ref |
| **Timer hits zero** | Toast notification; no automatic submit (user must answer) |
| **Chat SSE parse errors** | Malformed chunks skipped; stream errors surfaced in toast |
| **Document expiry (2 h)** | Cleanup worker removes stale uploads |
| **Tutor agent init failure** | Lazy init prevents startup crash; learning routes degrade gracefully |
| **Empty `model_name` / `api_key` in request** | Treated as absent; system model used |
| **Session storage init cache stale** | Full state in `sessionStorage` may lack fixes until new demo started |

---

## Academic Work

Stud sits at the intersection of **medical education**, **serious games**, and **multi-agent LLM systems**. The design reflects several research-aligned principles:

### Pedagogical grounding

- **Situated learning:** Cases embed learners in a generated clinical world (setting, resources, era) rather than isolated vignettes.
- **Formative assessment:** `PerformanceAnalysis` captures score, narrative feedback, strengths, and weaknesses per case—not just binary correctness.
- **Progressive difficulty:** State Controller escalation ties narrative changes to answer quality, clue usage, and time pressure.

### Software engineering contribution

- **Agent specialization** as an alternative to monolithic clinical simulators.
- **Typed state machines** for LLM-driven games, with explicit handoff between State Controller and Game Master at `max_clinical_changes`.
- **Client–server state reconciliation** patterns for rich Pydantic models consumed by thin UI layers.

### Document-driven extension (design research)

`python_backend/about/document-driven-mediquest-design.md` analyzes a **document-grounded Mediquest** pipeline: chunk ingestion → relevance scoring → bounded parallel generation → sequential `game_id` consumption. This documents scale limits (chunk size, worker queues, durable ordering) for curriculum-aligned adventures derived from uploaded texts—relevant to **RAG + serious games** research.

### Creator & mission

Built by **Dr. Jeffrey Otoibhi**, Stud applies clinical domain expertise to healthcare technology: gamified training, AI-assisted study, and assessment tooling intended for healthcare professionals globally.

Related in-repo documentation:

- `python_backend/about/mediquest-workflow.md` — Game lifecycle
- `python_backend/about/learning-workflow.md` — RAG study mode
- `python_backend/about/quiz-workflow.md` — Assessment flow
- `python_backend/about/production-scaling-50k-dau.md` — Scale planning

---

## Tech Stack

| Layer | Technologies |
|-------|----------------|
| **Frontend** | Next.js 16, React 18, TypeScript, Tailwind CSS, Radix UI, Framer Motion |
| **Backend** | FastAPI, Pydantic v2, Pydantic-AI, Uvicorn/Gunicorn |
| **AI** | OpenRouter, Google Gemini, OpenAI (user-selectable) |
| **Data** | Supabase (PostgreSQL), Redis, pgvector / Pinecone |
| **Auth** | JWT (python-jose), bcrypt, Fernet encryption |
| **Infra** | Docker Compose, Traefik (Dokploy), optional AWS S3 |

---

## Project Structure

```
Stud/
├── frontend/                 # Next.js app (run dev server here)
│   ├── app/
│   │   ├── mediquest/        # Game UI
│   │   ├── demo/             # Demo launcher
│   │   ├── study/            # Document chat
│   │   ├── quiz/             # Quiz mode
│   │   ├── dashboard/        # User hub
│   │   └── api/              # BFF proxy routes
│   └── app/lib/              # game-state.ts, proxy.ts, auth.ts
├── python_backend/
│   ├── agents/               # AI agents
│   ├── api/                  # FastAPI routers
│   ├── models/               # Pydantic state models
│   ├── service/              # DB, Redis, crypto, documents
│   ├── about/                # Architecture & workflow docs
│   └── db/scripts/           # SQL migrations
└── tests/ai_tests/           # Integration tests vs live API
```

---

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker (recommended for backend + Redis)
- Supabase project and LLM API keys

### Backend (Docker)

```bash
cd python_backend
cp .env.example .env   # configure SUPABASE_*, SECRET_KEY, model keys
docker-compose -f docker-compose.local.yml up
# API → http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
# .env.local: PYTHON_BACKEND_URL=http://localhost:8000
npm run dev
# App → http://localhost:3000
```

### Run tests

```bash
pip install -r tests/ai_tests/requirements-ai.txt
pytest tests/ai_tests -v
```

---

## Further Documentation

| Document | Description |
|----------|-------------|
| [python_backend/about/README.md](python_backend/about/README.md) | Backend doc index |
| [python_backend/about/core-features.md](python_backend/about/core-features.md) | Feature overview |
| [python_backend/about/mediquest-workflow.md](python_backend/about/mediquest-workflow.md) | Game API workflow |
| [python_backend/about/capacity-and-scaling.md](python_backend/about/capacity-and-scaling.md) | Bottlenecks & scaling |
| [frontend/DEPLOYMENT_GUIDE.md](frontend/DEPLOYMENT_GUIDE.md) | Frontend deploy |
| [python_backend/DOCUMENT_PROCESSING_GUIDE.md](python_backend/DOCUMENT_PROCESSING_GUIDE.md) | Ingestion pipeline |

---

## License

Proprietary — All rights reserved.
