# Production Scaling Guide — 50k DAU (AI / Game Chat)

Structured reference for infrastructure, cost, and capacity when **daily active users (DAU)** is the target metric and **AI/game chat** is the main traffic.

**Related:** [capacity-and-scaling.md](./capacity-and-scaling.md) (single-server estimates), [core-features.md](./core-features.md).

---

## 1. Definitions

| Term | Meaning for Stud |
|------|------------------|
| **50k DAU** | ~50,000 users with meaningful activity per day — **not** 50k online at once |
| **Peak concurrent** | Users active at the same moment during busy hour |
| **In-flight AI requests** | HTTP requests waiting on LLM + cache + DB (often 3–15s each) |

**Planning conversion (chat-heavy edu/game):**

| Metric | Typical range @ 50k DAU |
|--------|-------------------------|
| Peak concurrent users | **~500–1,500** (~1–3% of DAU; spikes can be higher) |
| In-flight AI requests at peak | **~200–800** |
| Messages per day | **~250k–1.5M+** (sessions/day × turns/session) |

The comment in `service/database.py` about “50k concurrent” is an **async threading goal**, not proven single-box capacity. [capacity-and-scaling.md](./capacity-and-scaling.md) documents **~50–100 concurrent** on one **8 GB / 2 vCPU** server for medium AI/chat load.

---

## 2. What limits you first (chat-first)

1. **LLM APIs** — rate limits, latency, and **cost** (usually the largest line item).
2. **App servers** — workers and memory held for seconds per chat turn.
3. **Redis** — hot sessions, queues, locks (required for multi-worker production).
4. **Supabase / Postgres** — durable game state and chat rows; load drops when Redis caches well.

Game chat routes are **not** rate-limited today (auth/upload are). At scale, add per-user / global limits using existing `api/rate_limit.py` + Redis.

---

## 3. Supabase vs self-hosted Postgres

### How the app connects today

The backend uses **Supabase over HTTP** (`supabase-py`), not a direct Postgres pool:

```python
# service/database.py
self.client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
```

Moving to “Postgres in Docker” requires **asyncpg (or similar)**, PgBouncer, backups, and likely changes to auth/storage — not a URL swap.

### Comparison @ 50k DAU

| | **Supabase (managed)** | **Postgres in Docker on app VPS** |
|--|------------------------|-----------------------------------|
| **Fit** | Good with Redis caching hot reads | Poor on same host as API under chat load |
| **Cash** | Pro **$25+** → often Team / compute add-ons | VPS **$80–300/mo** + operational time |
| **Risk** | Predictable | Single disk, no HA unless you build it |
| **Recommendation** | **Default** until Supabase bill + refactor pain justify move | Only as **dedicated DB VM** with ops expertise |

**Bottom line:** For 50k DAU chat-first, **keep Supabase** (or managed Postgres on a **separate** host). Savings usually come from **Redis**, fewer DB round-trips, and **LLM cost control**, not dropping Supabase alone.

---

## 4. Redis

### Role in Stud

| Use | Location / notes |
|-----|------------------|
| Game / GM / NPC chat cache | `utils.py`, `redis_service.py` — **1h TTL** |
| Game state cache | `game_state:{id}`, session blobs |
| User profile cache | `auth_deps.py` — short TTL |
| Document-game job queue | `document_job_queue.py` — `RPUSH` / `BLPOP` |
| Cleanup lock | `cleanup_service.py` — one worker per cycle |
| Rate limits | `api/rate_limit.py` (auth/upload today) |

If Redis is unavailable, the app **degrades** (warnings, more Supabase traffic) — not a hard stop.

### Redis vs Supabase

- **Supabase** = durable truth.
- **Redis** = hot path for **active** games (minutes–hours), queues, locks.

### Sizing @ 50k DAU (chat-heavy)

| Item | Estimate |
|------|----------|
| Active game state JSON | **50–200 KB** / session |
| Chat history | **20–100 KB** / conversation (1h TTL helps) |
| **RAM (safe)** | **~4 GB** Redis instance (headroom for spikes + fragmentation) |
| **Connections** | Lower **`REDIS_MAX_CONNECTIONS`** per API node (e.g. **30–50**), not 200 × many servers |

### Docker Redis (current Compose) vs production

| | **Compose `redis:7-alpine`** | **Managed / dedicated Redis** |
|--|------------------------------|--------------------------------|
| **Good for** | Dev, single-node | **50k DAU**, multiple API instances |
| **Production** | One shared URL on same network | **4 GB**, HA optional, **not** on app boxes |

**Cost (order of magnitude):** **$30–150/mo** managed or dedicated — small vs LLM + app fleet.

**Env (Docker Compose backend):**

```env
REDIS_URL=redis://redis:6379
REDIS_HOST=redis
```

Backend on host only: `redis://localhost:6379`.

---

## 5. Minimum hardware architecture @ 50k DAU

Think **roles**, not one VPS.

| Role | Target setup |
|------|----------------|
| **API** | **6–10×** `4 vCPU, 8 GB RAM` behind a load balancer (~75–100 chat users / node at peak) |
| **Redis** | **1× dedicated** `2–4 GB` (managed or separate VM) |
| **Database** | **Supabase Pro → Team/compute** or managed Postgres **8–16 GB** + pooler |
| **Load balancer** | Nginx / ALB / Cloudflare |

**Early growth (not full 50k DAU peak):** 2× `8 GB / 4 vCPU` API + Redis + Supabase Pro.

**Rough infra only (no LLM):** **~$400–1,500+/month** (region-dependent).

### Single-server baseline (from capacity doc)

| Server | Concurrent active | DAU (illustrative) |
|--------|-------------------|---------------------|
| 8 GB / 2 vCPU | 50–100 | 200–500 |
| 16 GB / 4 vCPU | 120–200 | 500–1k |
| 32 GB / 8 vCPU | 250–400 | 1k–2k |

50k DAU ⇒ **horizontal scaling**, not one bigger box.

---

## 6. LLM cost (dominant)

Illustrative — model with real analytics:

- 50k DAU × **15 turns/day** ≈ **750k LLM calls/day**
- ~**3k tokens** / turn ⇒ **~2B tokens/day** possible
- **~$6k–30k+/month** possible before enterprise discounts — often **exceeds** infra

Architect for: shorter prompts, caching, cheaper models for simple steps, **queues**, per-user concurrency caps.

---

## 7. Process restarts and production server

| Layer | Behavior |
|-------|----------|
| **Request errors (5xx)** | Process **keeps running** |
| **Gunicorn worker crash** | Master **respawns worker** (if Gunicorn is used) |
| **Main process exit** | Docker `restart: unless-stopped` **restarts container** |
| **`start.sh` retry loop** | **Does not run** after crash — `exec` replaces shell; Docker handles restart |
| **Default Compose without `GUNICORN_WORKERS`** | **Uvicorn `--reload`** (dev) — reloads on file change, **not** on runtime errors |

**Production in Docker:** set `GUNICORN_WORKERS=4` and install **`gunicorn`** (see `requirements.txt`). Rebuild image after dependency changes.

---

## 8. Roadmap by growth stage

### Now → ~2k DAU

- 1× `8 GB / 2–4 vCPU` API, Redis (Compose or small dedicated), Supabase Pro
- `GUNICORN_WORKERS=4`, `gunicorn` in `requirements.txt`
- Rate limits on **game/chat** endpoints

### ~2k–10k DAU

- 2–3 API instances, dedicated Redis, monitor p95 chat latency and LLM 429s

### Toward 50k DAU

- **6–10** API nodes, **4 GB** shared Redis, scaled Supabase tier
- Global cap on in-flight LLM work per instance
- Keep document-game heavy work in **Redis queue** workers (`document_job_queue.py`)

---

## 9. Docker / Gunicorn troubleshooting

### Symptom

```text
start.sh: line 82: exec: gunicorn: not found
stud-backend exited with code 127 (restarting)
```

### Cause

`GUNICORN_WORKERS` is set (e.g. `4`) but **`gunicorn` was not installed** in the image (`requirements.txt`).

### Fix

1. Ensure `gunicorn` is listed in `python_backend/requirements.txt`.
2. Rebuild and restart:

```bash
cd python_backend
docker compose build --no-cache backend
docker compose up -d
```

3. Confirm logs show Gunicorn starting without exit 127.

### Dev vs prod in `start.sh`

| `GUNICORN_WORKERS` | Mode |
|--------------------|------|
| Unset or empty | Uvicorn `--reload` (development) |
| Positive integer (e.g. `4`) | Gunicorn + `UvicornWorker` (production) |

---

## 10. Quick reference — env vars

| Variable | Purpose |
|----------|---------|
| `REDIS_URL` | Redis connection (Compose: `redis://redis:6379`) |
| `REDIS_MAX_CONNECTIONS` | Per-process pool cap (lower at scale) |
| `GUNICORN_WORKERS` | Enable production multi-worker server |
| `GUNICORN_TIMEOUT` | Worker timeout (default 120s; long AI turns) |
| `DB_THREAD_POOL_SIZE` | Thread pool for Supabase `to_thread` calls |

---

**Last updated:** 2026-05-21
