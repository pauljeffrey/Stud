"""
Model getter functions for agents.

Every getter follows the same pattern:
  1. If user-supplied model_name + api_key are provided, try those first.
  2. Otherwise fall back to the agent-specific env-var config.
  3. If the user model fails to initialise, ``select_model_with_fallback`` falls
     back to the system default automatically.
"""
import os
from typing import Optional, Tuple

from model import select_model, select_model_with_fallback
from configs.config import config
from service.model_credentials import validate_user_credentials

_DEFAULT_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"


def _env_model(config_attr: str) -> str:
    return getattr(config, config_attr, None) or os.getenv("MODEL_NAME") or _DEFAULT_MODEL


def _resolve_model(
    model_name: Optional[str],
    api_key: Optional[str],
    config_attr: str,
    *,
    allow_platform_fallback: bool = True,
):
    if model_name and api_key:
        ok, _ = validate_user_credentials(model_name, api_key)
        if ok:
            model, _ = select_model_with_fallback(
                model_name,
                api_key,
                allow_platform_fallback=allow_platform_fallback,
            )
            return model
    sys_name = _env_model(config_attr)
    model, _ = select_model(sys_name, os.getenv("OPENROUTER_API_KEY") or "")
    return model


def resolve_agent_credentials(
    model_name: Optional[str],
    api_key: Optional[str],
    provider: Optional[str],
    *,
    is_demo: bool,
) -> Tuple[Optional[str], Optional[str], str]:
    """Strip invalid user creds for demo; raise for registered users."""
    from service.model_credentials import resolve_game_credentials

    resolved = resolve_game_credentials(
        is_demo=is_demo,
        model_name=model_name,
        api_key=api_key,
        provider=provider,
    )
    return resolved.model_name, resolved.api_key, resolved.provider


def get_game_master_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    return _resolve_model(model_name, api_key, "GAME_MASTER_MODEL_NAME")


def get_game_world_model_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    return _resolve_model(model_name, api_key, "GAME_WORLD_MODEL_NAME")


def get_npc_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    return _resolve_model(model_name, api_key, "NPC_MODEL_NAME")


def get_state_controller_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    return _resolve_model(model_name, api_key, "STATE_CONTROLLER_MODEL_NAME")


def get_quiz_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    return _resolve_model(model_name, api_key, "QUIZ_MODEL_NAME")


def get_achievement_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    return _resolve_model(model_name, api_key, "GAME_MASTER_MODEL_NAME")
