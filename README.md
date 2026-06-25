# Stud

**Master Medicine Through Adventure**

Stud is a gamified medical education platform that combines multi-agent AI orchestration, structured clinical state management, and immersive UI to turn healthcare learning into an interactive role-playing experience. It supports three learning modes: **Mediquest** (clinical adventures), **Study** (document-grounded chat), and **Quiz** (assessment) behind a unified FastAPI backend and Next.js frontend.

---

## Table of Contents

- [Overview](#overview)
- [Decision & Idea Choices](#decision--idea-choices)
- [Architectural Choices](#architectural-choices)
- [Multi-Agent Workflow & Design](#multi-agent-workflow--design)
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

**Choice:** Frame medical education as a role-playing adventure with timers, clues, NPCs, achievements, and escalating cases not as a linear quiz app.

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

**Choice:** Represent game progress in typed models (`GameState`, `CaseState`, `PerformanceAnalysis` etc) with a shared `CommonFields` abstraction for repeated metadata.

**Rationale:** LLM outputs are validated and normalized before persistence. The API and frontend share a predictable schema instead of ad-hoc JSON blobs.

### 4. Bring-your-own-key (BYOK) with platform fallback

**Choice:** Users may supply their own model name and API key (encrypted at rest); the backend falls back to system-configured models when user credentials are missing or invalid.

**Rationale:** Reduces platform LLM cost for power users, supports model preference, and keeps demo/onboarding functional without mandatory key setup.
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


### Authentication & security

- Custom JWT + bcrypt (not Supabase Auth); sessions stored in `user_sessions` with best-effort writes so auth never hard-fails on missing tables.
- API keys encrypted with **Fernet (AES-128-CBC + HMAC)** before Supabase storage; legacy plain-text values still decrypt.
- Rate limiting with **fail-open** wrapper so Redis outages do not block login.

### Deployment

- **Backend:** Docker Compose
- **Frontend:** Vercel-compatible Next.js build.

---

## Multi-Agent Workflow & Design

Stud uses a **specialized multi-agent architecture** built on [Pydantic-AI](https://ai.pydantic.dev/). Each agent owns a narrow domain, produces typed Pydantic outputs, and is invoked by FastAPI routers not by other agents calling each other directly in most paths. The **Game Master** acts as the orchestrator for Mediquest.

### Agent roster

| Agent | Module | Primary responsibility |
|-------|--------|------------------------|
| **Game World Agent** | `agents/game_world_agent.py` | Immersive setting from `GameConfig` (profession, era, hospital, resources) | 
| **Game Master Agent** | `agents/game_master.py` | Case metadata, achievements, player chat, world updates, handoff orchestration |
| **State Controller Agent** | `agents/state_controller_agent.py` | Case escalation/de-escalation from answers, clues, dice, time pressure |
| **NPC Agent** | `agents/npc_agent.py` | Batch NPC generation + in-character dialogue |
| **Achievement Sub-agent** | `agents/achievement_subagent.py` | Career/promotion/reward achievements after case completion |
| **Tutor Agent** | `agents/tutor_agent.py` | Document-grounded study chat (RAG) |
| **Quiz Agent** | `agents/quiz_agent.py` | Quiz generation and open-ended scoring |
| **File Parser Agent** | `agents/file_parser_agent.py` | Extract text from uploaded documents |

Models are resolved per agent via `agents/agents.py` (`get_game_master_model`, `get_npc_model`, etc.), with **user BYOK** or **system fallback** through `select_model_with_fallback()` in `model.py`.

---
## Engineering Bottlenecks
### 1. External LLM latency and rate limits

The backend is **I/O-bound**: most request time waits on OpenRouter, Gemini, or OpenAI. Game initialization alone may invoke the Game World Agent, Game Master, State Controller, and NPC Agent in sequence—often **10–30+ seconds** on cold paths.

**Mitigations implemented:** OpenRouter prompt caching, dedicated init agents (tool-free paths to avoid extra LLM round-trips), character-chunk SSE streaming for perceived responsiveness, `select_model_with_fallback()` for resilient model selection.

### 2. Multi-step game initialization

Each new Mediquest session triggers world creation, case generation, and NPC batch generation. This is inherently expensive and difficult to parallelize fully because later steps depend on earlier outputs.

**Mitigations:** Redis session cache returns quickly after init; init payload cached in `sessionStorage` on the client to skip re-fetch; background DB persist so HTTP response is not blocked.


### 3. Document processing spikes

Uploading and chunking PDFs/DOCX/PPT is **CPU- and memory-intensive** (100–300 MB per heavy request per internal capacity docs).

**Mitigations:** 2-hour expiry for free-tier documents, cleanup worker on startup, lazy tutor agent init so model errors do not crash the entire app.

---

## Trade-offs

| Decision | Benefit | Cost |
|----------|---------|------|
| **Multi-agent vs single agent** | Clear prompts, modular testing, per-agent models | Higher init latency, more moving parts |
| **Pydantic-strict game state** | Type safety, fewer silent data bugs | Client must send complete backend fields |
| **Redis cache** | Fast session reads, demo support | Optional dependency; cache/DB can diverge briefly |
| **BYOK** | User cost control, model choice | Encryption key management; support burden |
| **SSE streaming** | Responsive chat UX | Harder error handling |
| **Concise generation prompts** | Faster tokens, cleaner UI | Less narrative richness per case |

---


```bash
pip install -r tests/ai_tests/requirements-ai.txt
pytest tests/ai_tests -v
```
## Performance expectations (indicative)

From internal capacity analysis (`python_backend/about/capacity-and-scaling.md`):

- Light API: tens of ms (excluding LLM)
- Agent call: 2–10 s per LLM round-trip
- Game init: often 15–45 s depending on model and provider
- Document upload/process: seconds to minutes by file size

---

## Tech Stack

| Layer | Technologies |
|-------|----------------|
| **Frontend** | Next.js 16, React 18, TypeScript, Tailwind CSS, Radix UI, Framer Motion |
| **Backend** | FastAPI, Pydantic v2, Pydantic-AI, Uvicorn/Gunicorn |
| **AI** | OpenRouter, Google Gemini, OpenAI (user-selectable) |
| **Data** | Supabase (PostgreSQL), Redis, pgvector / Pinecone |
| **Auth** | JWT, bcrypt, Fernet encryption |
| **Infra** | Docker Compose, optional AWS S3 |

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
cp .env.example .env   # configure SUPABASE_*, SECRET_KEY, model keys etc
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

