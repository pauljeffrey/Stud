"""Parse game-state payloads sent by the Next.js client."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from models.states import CaseState, GameState, GameWorldModel, NPCState

_CLIENT_ONLY_KEYS = frozenset({"game_master_chat_history"})


def normalize_id(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_npc_list(raw: Any) -> List[NPCState]:
    if not raw:
        return []
    if not isinstance(raw, list):
        raw = [raw]
    parsed: List[NPCState] = []
    for item in raw:
        if isinstance(item, NPCState):
            parsed.append(item)
        elif isinstance(item, dict):
            parsed.append(NPCState.model_validate(item))
    return parsed


def find_npc(npc_states: Any, npc_id: str) -> Optional[NPCState]:
    target = normalize_id(npc_id)
    if not target:
        return None
    for npc in parse_npc_list(npc_states):
        if normalize_id(npc.npc_id) == target:
            return npc
    return None


def parse_client_game_state(raw: Dict[str, Any]) -> GameState:
    """Rebuild a GameState from the client payload (preserves backend-only fields)."""
    data = deepcopy(raw)

    for key in _CLIENT_ONLY_KEYS:
        data.pop(key, None)

    case_state = data.get("case_state")
    if not isinstance(case_state, dict):
        case_state = {}

    top_npcs = data.pop("npc_states", None)
    if top_npcs and not case_state.get("npc_states"):
        case_state["npc_states"] = top_npcs

    if case_state.get("examination_findings") and not case_state.get("investigations"):
        case_state["investigations"] = case_state["examination_findings"]
    if case_state.get("investigation_results") and not case_state.get("scan_images"):
        case_state["scan_images"] = case_state["investigation_results"]

    if not case_state.get("investigations"):
        case_state["investigations"] = {"result": []}
    elif isinstance(case_state["investigations"], dict) and "result" not in case_state["investigations"]:
        case_state["investigations"] = {"result": []}

    if not case_state.get("scan_images"):
        case_state["scan_images"] = {"result": []}
    elif isinstance(case_state["scan_images"], dict) and "result" not in case_state["scan_images"]:
        case_state["scan_images"] = {"result": []}

    case_state.pop("examination_findings", None)
    case_state.pop("investigation_results", None)

    case = CaseState.model_validate(case_state)
    if case.npc_states:
        case.npc_states = parse_npc_list(case.npc_states)
    data["case_state"] = case

    gw = data.get("game_world")
    if isinstance(gw, dict):
        data["game_world"] = GameWorldModel.model_validate(gw)

    return GameState(**data)
