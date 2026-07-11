"""Validate and resolve per-user AI model credentials."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

from configs.config import config

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MODEL_HINT_RE = re.compile(
    r"(gemini|gpt|claude|openai|anthropic|llama|mistral|nemotron|/|meta-)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ResolvedModelCredentials:
    model_name: str
    api_key: str
    provider: str
    used_platform_default: bool = False


def looks_like_email(value: str) -> bool:
    return bool(_EMAIL_RE.match((value or "").strip()))


def is_plausible_api_key(value: str) -> bool:
    key = (value or "").strip()
    if len(key) < 8:
        return False
    if looks_like_email(key):
        return False
    return True


def is_plausible_model_name(value: str) -> bool:
    name = (value or "").strip()
    if len(name) < 3:
        return False
    if looks_like_email(name):
        return False
    return bool(_MODEL_HINT_RE.search(name))


def validate_user_credentials(
    model_name: Optional[str],
    api_key: Optional[str],
    provider: Optional[str] = None,
) -> tuple[bool, str]:
    """Return (ok, user-facing reason). Both model_name and api_key are required."""
    name = (model_name or "").strip()
    key = (api_key or "").strip()

    if not name and not key:
        return False, "Model name and API key are required."

    if not name:
        return False, "Model name is required. See our API key guide for examples."

    if not key:
        return False, "API key is required. It was not supplied or is empty."

    if looks_like_email(name):
        return False, "Model name cannot be an email address. Use a model ID such as gemini-2.0-flash or gpt-4o-mini."

    if looks_like_email(key):
        return False, "API key cannot be an email address. Paste the key from your AI provider."

    if not is_plausible_model_name(name):
        return False, (
            "Model name does not look valid. Examples: gemini-2.0-flash, gpt-4o-mini, "
            "anthropic/claude-3.5-sonnet, meta-llama/llama-3.3-70b-instruct:free"
        )

    if not is_plausible_api_key(key):
        return False, "API key is too short or invalid."

    if provider and provider.lower() not in {"google", "openai", "anthropic", "gemini", "openrouter"}:
        return False, f"Unsupported provider: {provider}"

    return True, ""


def platform_default_credentials() -> ResolvedModelCredentials:
    model_name = (
        getattr(config, "GAME_MASTER_MODEL_NAME", None)
        or os.getenv("MODEL_NAME")
        or "nvidia/nemotron-3-nano-30b-a3b:free"
    )
    api_key = (
        os.getenv("OPENROUTER_API_KEY")
        or os.getenv("MODEL_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or ""
    )
    return ResolvedModelCredentials(
        model_name=model_name,
        api_key=api_key,
        provider="openrouter" if "/" in model_name else "google",
        used_platform_default=True,
    )


def resolve_game_credentials(
    *,
    is_demo: bool,
    model_name: Optional[str],
    api_key: Optional[str],
    provider: Optional[str] = "google",
) -> ResolvedModelCredentials:
    """Demo: invalid/missing user creds → platform .env default. Registered: must be valid."""
    ok, reason = validate_user_credentials(model_name, api_key, provider)
    if ok:
        return ResolvedModelCredentials(
            model_name=(model_name or "").strip(),
            api_key=(api_key or "").strip(),
            provider=(provider or "google").lower(),
            used_platform_default=False,
        )

    if is_demo:
        return platform_default_credentials()

    raise ValueError(reason)
