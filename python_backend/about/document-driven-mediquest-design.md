# Document-Driven Mediquest: Design Analysis & Scale Recommendations

This document captures an architectural and operational analysis for a **document-grounded** Mediquest mode (`from_document` + `document_id`), including chunk-based case generation, sequential game-state consumption, and implications for **high scale** (thousands to millions of users). It is intended for backend engineers and product owners planning implementation and capacity.

---

## 1. Target design (summary)

A dedicated flow branches when the game is spawned or updated from an **uploaded document** rather than from generic world configuration alone:

- **Game world** is still generated (or reused) to anchor tone and setting.
- **Chunks** of document text (with a **minimum size target**, e.g. ~5,000 words per logical segment) are loaded using `document_id` from storage/DB.
- For each segment, the system may produce **structured objects** combining:
  - **`ClinicalCaseMetadata`**
  - **Relevance score** (importance to fundamental understanding of the material)
  - **Difficulty level** (with a planned default, e.g. 15 per chunk in the sketch—subject to product/schema alignment)
- **Multiprocessing / parallel API calls** are used to generate these objects across chunks (with **bounded** concurrency in production).
- **Relevance** filters out insignificant cases first.
- A **refinement** step uses the same (or a sibling) agent with **game world description**, processes cases **per chunk** sequentially/iteratively, and may expose tools such as:
  - **`fetch_chunk`** — retrieve raw chunk text for refinement
  - **`save_to_game_state`** — persist generated states and build an ordered list of `game_id`s for sequential play
- **Document mode** caps **maximum cases** (e.g. **20** for v1).
- Game Master methods (`initialize_game`, `generate_clinical_case`, `update_game`, `update_clinical_case` / `update_clinical_state`, `handoff_from_state_controller`, `update_game_world`) accept **`from_document`** and **`document_id`** to branch into this pipeline vs. the classic path.
- **`update_clinical_case`** (state controller path) may use **document_id + chunk identifier** to fetch chunk text and keep clinical updates **coherent** with source material.
- **Sequential access**: a **list of `game_id`s** (or equivalent) drives which pre-generated `GameState` is used when `update_game` and related logic run.

---

## 2. What works well

| Aspect | Rationale |
|--------|-----------|
| **Explicit mode flags** | `from_document` + `document_id` make behavior predictable, testable, and easy to log/meter separately from “freeform” games. |
| **Chunk → metadata → filter → refine** | Matches common RAG/curriculum patterns: local evidence first, then global quality and deduplication. |
| **Bounded case count (e.g. 20)** | Caps per-upload cost, latency, and storage; important for a first release. |
| **Sequential consumption of pre-generated states** | Avoids re-running the heaviest generation on every `update_game` if states are **materialized once** and then **walked in order**. |

---

## 3. Critical issues at scale (thousands to millions of users)

### 3.1 Chunk size: “minimum 5,000 words” vs typical RAG

- Many systems use **smaller** chunks (hundreds of tokens) for retrieval and embedding.
- **Very large** chunks (multi-thousand words) imply:
  - **Fewer** parallel units per document → coarser scheduling and **longer** single LLM contexts.
  - Higher risk of **one chunk mixing** unrelated ideas → noisier relevance scores and **harder deduplication**.

**Recommendation:** Either (a) **define a “segment”** as an explicit merge of smaller stored chunks up to a word budget, with **stable segment IDs**, or (b) keep **smaller** persisted chunks and let generation agents **pull** multiple adjacent chunks when needed. Avoid silently assuming one DB chunk row equals one 5k-word block unless your ingestion layer guarantees that.

### 3.2 Parallelism: multiprocessing and “many API calls at once”

- Per upload, *chunks × calls* can create **spikes** in:
  - Provider **rate limits**
  - **Internal** worker and DB connection limits
  - **Queue depth** (everyone else waits)

**Recommendation:**

- **Bounded concurrency** (per job and globally), **queues** (Celery, RQ, Arq, cloud-native workers), and **idempotent job IDs** so retries do not **double-bill** LLM calls.
- Prefer **async job execution** for anything longer than a few seconds; return **202 + job_id** and poll/stream progress.

### 3.3 Writing many `game_state` rows “as they arrive”

- Creating **many partial** rows can multiply **write load**, complicate **rollback**, and make **consistency** harder (half-built adventures).

**Recommendation:** Prefer a **job** or **session** record with **stages** and **batched** persistence; use **object storage** for large intermediate JSON if needed. Promote to canonical **`game_states`** when a case is **complete** (unless the product **requires** row-per-chunk for UX).

### 3.4 “List of `game_id`s in deps” (agent context)

- In-memory **deps** are **not durable** across:
  - Process restarts
  - Horizontal scale-out (next request hits another instance)
  - Long async jobs

**Recommendation:** Persist **`ordered_game_ids`**, **`current_index`**, **`document_id`**, and mode flags in **DB** (or Redis with TTL and durability policy) keyed by **session** or **primary adventure id**. Reload on every request/worker step.

### 3.5 Refinement loops (tools, iterative LLM)

- **Iterative** tool + LLM loops are **token-heavy** and **slow** at scale.

**Recommendation:** Add **non-LLM** dedup/relevance (e.g. **embeddings**, **MinHash**/similarity on scenario text) where possible, cap **max tool rounds**, and run refinement **in workers** with **budgets** per job.

### 3.6 Stable chunk identity

- `document_id + chunk_number` is fragile if:
  - Document is **reprocessed**
  - Chunk list **changes** (re-chunking)

**Recommendation:** Use **immutable chunk IDs** and optionally **content hashes**; version the ingested document when content changes.

---

## 4. Memory efficiency and speed

| Goal | Practice |
|------|----------|
| **Do not load full files in API workers** | Stream chunk text from DB/S3 **on demand** for the active step only. |
| **Limit concurrent LLM work per user/job** | Semaphores / queue limits; backpressure. |
| **Reuse expensive artifacts** | Cache **per-chunk embeddings** if used for relevance/dedup; key by `chunk_id`. |
| **Separate hot path** | Synchronous API for **start job + status**; **heavy** work only in workers. |
| **Storage layout** | Large JSON **artifacts** in object storage; DB holds **metadata + pointers** and small denormalized fields for list APIs. |

---

## 5. Token cost and abuse prevention

Aligns with a future **maximum file size** and operational limits (to be implemented in code/config):

- **Upload caps:** max bytes, max pages, max extracted **words** (or max chunks after ingest).
- **Per-job caps:** max LLM calls, max output tokens, max wall-clock time.
- **Per-user / per-org quotas:** daily or monthly **document game** generations.
- **Tiered behavior:** if budget is hit mid-job, **degrade** gracefully (e.g. fewer cases, skip refinement) with explicit **status** in the job record.

---

## 6. Where to pass `from_document` / `document_id` (Game Master and downstream)

A pragmatic rule: **pass flags where the function truly branches**; **avoid** duplicating them everywhere if a **single persisted context** (e.g. `DocumentGameJob` or session row) already carries `from_document`, `document_id`, queue state, and pointer into the case list.

| Function / area | Likely need explicit args? | Notes |
|-----------------|----------------------------|--------|
| **`initialize_game`** | **Yes** | Entry point: classic vs. document job bootstrap / load persisted plan. |
| **`generate_clinical_case`** | **Yes** | Classic generation vs. “next case from document pipeline / DB-backed spec.” |
| **`update_game`** | **Yes** | Classic vs. advancing **sequential** pre-materialized states. |
| **`update_clinical_case` / state path** | **Yes** (or context) | When grounding updates, **chunk text** may be required; `document_id` + stable **chunk id** matter. |
| **`handoff_from_state_controller`** | **Often redundant** if job/session state already encodes document mode; branch only if handoff **differs materially** (e.g. different next-case source). |
| **`update_game_world`** | **Optional** | Often world updates stay the same; document mode may only change **inputs** to prompts. If behavior is identical, **skip** extra parameters and read mode from **session/job**. |
| **`state_controller` / `npc` agents** | **As needed** | Thread context when prompts must cite **chunk** or **relevance**; otherwise inject via **CaseState** / **metadata** to keep agent signatures small. |

**Single “context object” (recommended at scale):** e.g. `DocumentGameContext` or `job_id` that resolves to DB row, reducing **parameter sprawl** and desync bugs.

---

## 7. Recommendations (prioritized)

1. **Durable state:** Persist ordered case/game IDs and cursor in **DB** (or equivalent), not only in agent deps.
2. **Chunking strategy:** Reconcile “5k word segments” with **actual** stored chunks; use **stable chunk IDs** and versioning.
3. **Execution model:** **Async jobs** + **bounded** parallelism; never unbounded `multiprocessing` in the API process.
4. **Dedup and filter:** Use **cheap** signals (embeddings/heuristics) before expensive LLM refinement; **cap** refinement rounds.
5. **Writes:** Batch or stage persistence; avoid **N partial game_states** unless product demands it.
6. **Quotas and limits:** File size, word count, cases per document, and per-user quotas—**enforced** before and during jobs.
7. **API contract:** For long runs, return **job_id** and expose **status** (and optional SSE) for **progress** without holding HTTP connections open indefinitely.

---

## 8. Relationship to other docs

- **[mediquest-workflow.md](./mediquest-workflow.md)** — End-to-end Mediquest flow (classic paths, APIs, handoff).
- This document — **Document-driven** branch, **scale**, and **operational** concerns for the same product surface.

When implementation lands, add cross-links from `mediquest-workflow.md` to the concrete endpoints, job schema, and chunk/segment model chosen in code.

---

## 9. Next implementation steps (non-binding checklist)

- Define **job** and **session** schema: `document_id`, `from_document`, `ordered_game_ids`, `current_index`, status, error, token usage.
- Define **chunk/segment** model: id, `document_id`, order, content hash, word count.
- Implement **ingest** limits (max file size, max words) and **refusal** before expensive work.
- Wire **Game Master** branches behind **`from_document`** with persistence tests (restart-safe).
- Add **observability**: metrics for job duration, LLM spend per job, and failure rate by stage.

---

*Last updated: design review for document-grounded Mediquest; refine numbers (e.g. default difficulty, word thresholds) to match product and schema in `models/states.py` as implementation proceeds.*
