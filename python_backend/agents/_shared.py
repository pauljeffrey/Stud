"""Small helpers shared across agent classes to avoid copy-pasted boilerplate."""
from typing import Optional, Tuple


def merge_credentials(
    current_model_name: Optional[str],
    current_api_key: Optional[str],
    new_model_name: Optional[str],
    new_api_key: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """Apply a partial credential update, keeping the current value for any field
    the caller didn't supply (mirrors the `_reinitialize_model` pattern every
    agent class uses when a request brings user-specific model/key overrides)."""
    model_name = new_model_name if new_model_name is not None else current_model_name
    api_key = new_api_key if new_api_key is not None else current_api_key
    return model_name, api_key
