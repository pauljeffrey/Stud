"""
Model getter functions for agents.

Every getter follows the same pattern:
  1. If user-supplied model_name + api_key are provided, try those first.
  2. Otherwise fall back to the agent-specific env-var config.
  3. If the user model fails to initialise, ``select_model_with_fallback`` falls
     back to the system default automatically.
"""
from typing import Optional
from model import select_model, select_model_with_fallback
from configs.config import config


def get_game_master_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for Game Master agent, with user-model fallback."""
    if model_name and api_key:
        model, _ = select_model_with_fallback(model_name, api_key)
        return model
    sys_name = getattr(config, 'GAME_MASTER_MODEL_NAME', None) or "gemini-2.0-flash"
    sys_key = getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(sys_name, sys_key)
    return model


def get_game_world_model_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for Game World agent, with user-model fallback."""
    if model_name and api_key:
        model, _ = select_model_with_fallback(model_name, api_key)
        return model
    sys_name = getattr(config, 'GAME_WORLD_MODEL_NAME', None) or "gemini-2.0-flash"
    sys_key = getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(sys_name, sys_key)
    return model


def get_npc_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for NPC agent, with user-model fallback."""
    if model_name and api_key:
        model, _ = select_model_with_fallback(model_name, api_key)
        return model
    sys_name = getattr(config, 'NPC_MODEL_NAME', None) or "gemini-2.0-flash"
    sys_key = getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(sys_name, sys_key)
    return model


def get_state_controller_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for State Controller agent, with user-model fallback."""
    if model_name and api_key:
        model, _ = select_model_with_fallback(model_name, api_key)
        return model
    sys_name = getattr(config, 'STATE_CONTROLLER_MODEL_NAME', None) or "gemini-2.0-flash"
    sys_key = getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(sys_name, sys_key)
    return model


def get_achievement_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for Achievement sub-agent, with user-model fallback."""
    if model_name and api_key:
        model, _ = select_model_with_fallback(model_name, api_key)
        return model
    sys_name = getattr(config, 'GAME_MASTER_MODEL_NAME', None) or "gemini-2.0-flash"
    sys_key = getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(sys_name, sys_key)
    return model


