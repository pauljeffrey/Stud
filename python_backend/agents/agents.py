"""
Model getter functions for agents
Provides a centralized way to get models for different agents
"""
from typing import Optional
from model import select_model
from configs.config import config


def get_game_master_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for Game Master agent"""
    model_name = model_name or getattr(config, 'GAME_MASTER_MODEL_NAME', None) or "gemini-2.0-flash"
    api_key = api_key or getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(model_name, api_key)
    return model


def get_game_world_model_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for Game World agent"""
    model_name = model_name or getattr(config, 'GAME_WORLD_MODEL_NAME', None) or "gemini-2.0-flash"
    api_key = api_key or getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(model_name, api_key)
    return model


def get_npc_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for NPC agent"""
    model_name = model_name or getattr(config, 'NPC_MODEL_NAME', None) or "gemini-2.0-flash"
    api_key = api_key or getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(model_name, api_key)
    return model


def get_state_controller_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for State Controller agent"""
    model_name = model_name or getattr(config, 'STATE_CONTROLLER_MODEL_NAME', None) or "gemini-2.0-flash"
    api_key = api_key or getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(model_name, api_key)
    return model


def get_achievement_model(model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Get model for Achievement sub-agent"""
    model_name = model_name or getattr(config, 'GAME_MASTER_MODEL_NAME', None) or "gemini-2.0-flash"
    api_key = api_key or getattr(config, 'GOOGLE_API_KEY', None) or ""
    model, _ = select_model(model_name, api_key)
    return model


