"""Run API/UI checks for previously untested Stud features."""
from __future__ import annotations

import json
import sys
import time
import uuid
import urllib.error
import urllib.request
from typing import Any

BASE = "http://localhost:3000"
BACKEND = "http://localhost:8001"
MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"
API_FIELDS = {"model_name": MODEL, "api_key": "test", "provider": "google"}

results: list[tuple[str, str, str]] = []  # name, status, detail


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, "PASS" if ok else "FAIL", detail[:300]))
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" — {detail[:120]}" if detail else ""))


def request_json(
    method: str,
    url: str,
    body: dict | None = None,
    headers: dict | None = None,
    timeout: int = 120,
) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def read_sse(url: str, body: dict, timeout: int = 120) -> tuple[bool, str]:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    chunks: list[str] = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for line in resp:
                line = line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = json.loads(line[5:].strip())
                if payload.get("error"):
                    return False, str(payload["error"])
                if payload.get("content"):
                    chunks.append(str(payload["content"]))
                if payload.get("complete"):
                    return True, "".join(chunks)
        return bool(chunks), "".join(chunks) or "no chunks"
    except Exception as e:
        return False, str(e)


def page_ok(path: str) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(f"{BASE}{path}")
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            return resp.status == 200, f"status={resp.status}, len={len(html)}"
    except Exception as e:
        return False, str(e)


def get_or_create_game() -> dict | None:
    # Try prior game from Redis
    game_id = "64da4002-bae6-4cfd-a734-1cbbae2c10c8"
    code, data = request_json("GET", f"{BASE}/api/game/{game_id}")
    if code == 200 and isinstance(data, dict) and data.get("game_state"):
        record("Reuse existing game", True, game_id)
        return data["game_state"]

    record("Reuse existing game", False, "expired — initializing new demo game")
    body = {
        "game_config": {"total_cases": 2, "max_clinical_changes": 3},
        "is_demo": True,
        "session_id": str(uuid.uuid4()),
        **API_FIELDS,
    }
    code, data = request_json("POST", f"{BASE}/api/game/initialize", body, timeout=300)
    if code != 200 or not isinstance(data, dict) or not data.get("game_state"):
        record("Create demo game for tests", False, f"HTTP {code}: {data}")
        return None
    record("Create demo game for tests", True, data["game_state"].get("game_id", ""))
    gs = data["game_state"]
    # merge init extras for downstream
    if data.get("npc_states"):
        cs = gs.setdefault("case_state", {})
        if isinstance(cs, dict):
            cs["npc_states"] = data["npc_states"]
        gs["npc_states"] = data["npc_states"]
    return gs


def main() -> int:
    print("=== UI page loads ===")
    for path in ["/demo", "/study", "/quiz", "/dashboard", "/auth/login", "/checkpoints"]:
        ok, detail = page_ok(path)
        record(f"Page {path}", ok, detail)

    # Mediquest without game_id should redirect client-side; server still returns 200
    ok, detail = page_ok("/mediquest")
    record("Page /mediquest", ok, detail)

    print("\n=== Auth (Supabase-dependent) ===")
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    code, reg = request_json(
        "POST",
        f"{BASE}/api/auth/register",
        {"email": email, "password": "TestPass123!", "name": "Test User", "user_type": "student"},
    )
    record("Auth register", code in (200, 201), f"HTTP {code}: {reg}")

    code, login = request_json(
        "POST",
        f"{BASE}/api/auth/login",
        {"email": email, "password": "TestPass123!"},
    )
    token = login.get("token") if isinstance(login, dict) else None
    record("Auth login", code == 200 and bool(token), f"HTTP {code}")

    auth_headers = {"Authorization": f"Bearer {token}"} if token else {}
    code, stats = request_json("GET", f"{BASE}/api/user/stats", headers=auth_headers)
    record("Dashboard user stats", code == 200, f"HTTP {code}: {stats if code != 200 else 'ok'}")

    print("\n=== Game endpoints ===")
    gs = get_or_create_game()
    if not gs:
        print("Skipping game endpoint tests — no game state")
    else:
        payload_base = {"game_state": gs, **API_FIELDS}

        code, clue = request_json("POST", f"{BASE}/api/game/use-clue", payload_base, timeout=180)
        record("Use clue", code == 200, f"HTTP {code}: {clue if code != 200 else 'clue_used=' + str(clue.get('game_state', {}).get('case_state', {}).get('clue_used'))}")
        if code == 200 and isinstance(clue, dict) and clue.get("game_state"):
            gs = clue["game_state"]

        ok, text = read_sse(
            f"{BASE}/api/game/master-chat",
            {**payload_base, "game_state": gs, "user_message": "What should I focus on in this case?"},
            timeout=180,
        )
        record("Game Master chat (SSE)", ok and len(text) > 0, text[:120] if not ok else f"{len(text)} chars")

        npc_id = None
        npcs = gs.get("npc_states") or (gs.get("case_state") or {}).get("npc_states") or []
        if npcs:
            npc_id = npcs[0].get("npc_id")
        if npc_id:
            ok, text = read_sse(
                f"{BASE}/api/game/npc-chat",
                {
                    **payload_base,
                    "game_state": gs,
                    "npc_id": npc_id,
                    "user_message": "Hello, how are you feeling today?",
                    "chat_history": [],
                },
                timeout=180,
            )
            record("NPC chat (SSE)", ok and len(text) > 0, text[:120] if not ok else f"{len(text)} chars")
        else:
            record("NPC chat (SSE)", False, "no npc_id in game state")

        code, upd = request_json(
            "POST",
            f"{BACKEND}/api/game/update-state",
            {**payload_base, "game_state": gs, "time_elapsed": 60, "clue_used": False},
            timeout=180,
        )
        record("Update case state (backend direct)", code == 200, f"HTTP {code}: {upd if code != 200 else 'handoff=' + str(upd.get('handoff_occurred'))}")
        if code == 200 and isinstance(upd, dict) and upd.get("game_state"):
            gs = upd["game_state"]

        code, dice = request_json(
            "POST",
            f"{BASE}/api/game/dice-effect",
            {"game_state": gs, "dice_result": 7, **API_FIELDS},
            timeout=180,
        )
        record("Dice effect", code == 200, f"HTTP {code}: {dice if code != 200 else dice.get('change_description', '')[:80]}")

        code, saved = request_json(
            "POST",
            f"{BASE}/api/game/save",
            {"game_state": gs, "user_id": gs.get("user_id")},
        )
        record("Save game (demo user)", code == 200, f"HTTP {code}: {saved if code != 200 else 'saved'}")

    print("\n=== Checkpoints ===")
    code, cp = request_json("GET", f"{BASE}/api/game/checkpoints", headers=auth_headers)
    record("Frontend checkpoints route", code == 404, f"HTTP {code} (expected missing proxy route)")

    if gs:
        code, sc = request_json(
            "POST",
            f"{BACKEND}/api/game/save-checkpoint?user_id={gs.get('user_id')}&game_state_id={gs.get('game_id')}&checkpoint_name=test-cp",
            timeout=30,
        )
        record("Backend save-checkpoint", code == 200, f"HTTP {code}: {sc}")

    print("\n=== Quiz ===")
    code, quiz = request_json(
        "POST",
        f"{BASE}/api/quiz/generate",
        {
            "quiz_type": "general",
            "num_questions": 3,
            "num_multiple_choice": 2,
            "num_open_ended": 1,
            "time_limit": 300,
            "source": "ai_knowledge",
            "user_id": "demo_test_user",
            "difficulty_level": "Medium",
            **API_FIELDS,
        },
        timeout=180,
    )
    record("Quiz generate", code == 200 and isinstance(quiz, dict) and quiz.get("success"), f"HTTP {code}")

    if code == 200 and isinstance(quiz, dict) and quiz.get("questions"):
        q0 = quiz["questions"][0]
        code, sub = request_json(
            "POST",
            f"{BASE}/api/quiz/submit",
            {
                "quiz_id": quiz.get("quiz_id"),
                "answers": {q0.get("id", "q1"): q0.get("options", ["A"])[0] if q0.get("options") else "test"},
                "user_id": "demo_test_user",
            },
            timeout=60,
        )
        record("Quiz submit", code == 200, f"HTTP {code}")

    code, score = request_json(
        "POST",
        f"{BACKEND}/api/quiz/score-open",
        {
            "question": "What is the first-line treatment for anaphylaxis?",
            "correct_answer": "Intramuscular epinephrine",
            "user_answer": "Epinephrine IM",
            **API_FIELDS,
        },
        timeout=120,
    )
    record("Quiz score-open (backend direct)", code == 200, f"HTTP {code}: {score if code != 200 else score.get('score')}")

    code, score_fe = request_json(
        "POST",
        f"{BASE}/api/quiz/score-open",
        {
            "question": "What is CPR compression rate?",
            "model_answer": "100-120 per minute",
            "user_answer": "About 110 per minute",
            **API_FIELDS,
        },
        timeout=30,
    )
    record("Quiz score-open (frontend proxy)", code != 404, f"HTTP {code} (404 = missing route)")

    print("\n=== Study mode ===")
    code, docs = request_json("GET", f"{BASE}/api/learning/documents?user_id=demo_test_user")
    record("Study list documents", code in (200, 401, 500), f"HTTP {code}")

    # Minimal text upload
    boundary = uuid.uuid4().hex
    file_content = b"Diabetes mellitus type 2 is managed with metformin as first-line therapy."
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="study_test.txt"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode() + file_content + f"\r\n--{boundary}\r\n".encode() + (
        f'Content-Disposition: form-data; name="user_id"\r\n\r\n'
        f"demo_test_user\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/api/learning/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            upload = json.loads(resp.read().decode())
            record("Study document upload", resp.status == 200, str(upload)[:120])
            doc_id = upload.get("document_id") or upload.get("id")
    except urllib.error.HTTPError as e:
        upload = e.read().decode()
        doc_id = None
        record("Study document upload", False, f"HTTP {e.code}: {upload[:120]}")

    if doc_id:
        ok, text = read_sse(
            f"{BASE}/api/learning/chat",
            {
                "document_id": doc_id,
                "user_id": "demo_test_user",
                "message": "What is first-line treatment mentioned in my notes?",
                **API_FIELDS,
            },
            timeout=180,
        )
        record("Study tutor chat (SSE)", ok, text[:120] if not ok else f"{len(text)} chars")

    print("\n=== Summary ===")
    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"Total: {len(results)} | Pass: {passed} | Fail: {failed}")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  FAIL: {name} — {detail}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
