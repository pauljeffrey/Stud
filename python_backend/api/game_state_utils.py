"""Parse game-state payloads sent by the Next.js client."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from models.states import GameState, GameWorldModel

_CLIENT_ONLY_KEYS = frozenset({"game_master_chat_history"})


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

    case_state.pop("examination_findings", None)
    case_state.pop("investigation_results", None)
    data["case_state"] = case_state

    gw = data.get("game_world")
    if isinstance(gw, dict):
        data["game_world"] = GameWorldModel.model_validate(gw)

    return GameState(**data)
