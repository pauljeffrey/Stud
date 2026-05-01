# AI / deployed-backend tests

These tests hit a **running** Stud Python API (FastAPI), typically from Docker (`python_backend/docker-compose.yml` exposes port **8000**).

## Install

From the repo root:

```bash
pip install -r tests/ai_tests/requirements-ai.txt
```

## Run

```bash
# Default: http://localhost:8000
pytest tests/ai_tests -v

# Deployed or different host
set BASE_URL=https://your-host.example
pytest tests/ai_tests -v
```

On Unix:

```bash
BASE_URL=http://localhost:8000 pytest tests/ai_tests -v
```

### Optional: LLM judge

Some tests call OpenAI when `OPENAI_API_KEY` or `JUDGE_API_KEY` is set. Without a key, judge steps are skipped or assertions are relaxed.

### Learning chat integration

`test_stud_learning_flow.py` needs a real document UUID in your database for `user_123`:

```bash
set STUD_TEST_DOCUMENT_ID=<uuid-from-documents-table>
pytest tests/ai_tests/test_stud_learning_flow.py -v
```

Without it, those tests are skipped.

## Scope

- **Stud today**: learning chat, health, `session_id` contract — not e-commerce. Commerce scenario groups are documented in `scenarios/COMMERCE_TEST_MATRIX.md` for a future service.
- **BASE_URL**: use `http://localhost:8000` for direct backend; use your Next.js origin only if you proxy `/api/*` to the same backend.

## Session ID

See `SESSION_ID.md` for how `session_id`, `enrollmentId`, and `documentId` interact in `/api/learning/chat`.
