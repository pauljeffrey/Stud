from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.settings import ModelSettings

from dotenv import load_dotenv
import logging
import os

from service.model_credentials import validate_user_credentials

load_dotenv()

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("MODEL_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Default OpenRouter settings — prompt caching reduces latency on repeat calls
_DEFAULT_OR_SETTINGS = OpenRouterModelSettings(
    openrouter_cache_instructions=True,
    openrouter_cache_messages=True,
    openrouter_cache_tool_definitions=True,
    timeout=float(os.getenv("MODEL_TIMEOUT", "180")),
)


def _base_model_settings() -> ModelSettings:
    return ModelSettings(timeout=float(os.getenv("MODEL_TIMEOUT", "180")))

_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"


def select_model(MODEL_NAME, API_KEY):
    """
    Select and initialize a model based on model name and API key.

    Routing logic:
      - Contains '/'          → OpenRouter  (e.g. 'nvidia/nemotron-…', 'anthropic/claude-…')
      - Contains 'gemini'     → Google Gemini
      - Contains 'claude'     → Anthropic direct
      - Contains 'gpt'/'openai' → OpenAI direct
      - Anything else         → OpenRouter (safe fallback, covers NVIDIA / Mistral / etc.)

    Returns:
        tuple: (model, agent)
    """
    if not MODEL_NAME:
        MODEL_NAME = _DEFAULT_MODEL

    MODEL_NAME_LOWER = MODEL_NAME.lower()

    if '/' in MODEL_NAME:
        # OpenRouter: covers nvidia/, anthropic/, openai/, mistral/, meta-llama/, …
        model = OpenRouterModel(
            MODEL_NAME,
            provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
            settings=_DEFAULT_OR_SETTINGS,
        )
    elif 'gemini' in MODEL_NAME_LOWER:
        gemini_key = API_KEY or GOOGLE_API_KEY
        model = GoogleModel(
            MODEL_NAME, provider=GoogleProvider(api_key=gemini_key), settings=_base_model_settings()
        )
    elif 'claude' in MODEL_NAME_LOWER:
        model = AnthropicModel(
            MODEL_NAME, provider=AnthropicProvider(api_key=API_KEY), settings=_base_model_settings()
        )
    elif 'gpt' in MODEL_NAME_LOWER or 'openai' in MODEL_NAME_LOWER:
        openai_key = API_KEY or OPENAI_API_KEY
        model = OpenAIChatModel(
            MODEL_NAME, provider=OpenAIProvider(api_key=openai_key), settings=_base_model_settings()
        )
    else:
        # Unknown name — route through OpenRouter; prefer the user's key when given
        or_key = API_KEY or OPENROUTER_API_KEY
        model = OpenRouterModel(
            MODEL_NAME,
            provider=OpenRouterProvider(api_key=or_key),
            settings=_DEFAULT_OR_SETTINGS,
        )

    agent = Agent(model)

    return model, agent


def _system_default_model():
    """Return the system-configured default model (from .env)."""
    return select_model(
        os.getenv("MODEL_NAME") or _DEFAULT_MODEL,
        os.getenv("OPENROUTER_API_KEY") or "",
    )


def select_model_with_fallback(
    user_model_name: str | None,
    user_api_key: str | None,
    *,
    allow_platform_fallback: bool = True,
):
    """Try user model/key; optionally fall back to the system default.

    Returns:
        tuple: (model, agent)
    """
    if user_model_name and user_api_key:
        ok, reason = validate_user_credentials(user_model_name, user_api_key)
        if ok:
            try:
                return select_model(user_model_name, user_api_key)
            except Exception as exc:
                if not allow_platform_fallback:
                    raise ValueError(
                        f"Could not initialise model '{user_model_name}'. Check the model name and API key."
                    ) from exc
                logger.warning(
                    "User model '%s' failed to initialise (%s) — falling back to system default.",
                    user_model_name,
                    exc,
                )
        elif not allow_platform_fallback:
            raise ValueError(reason)

    if not allow_platform_fallback:
        raise ValueError("Model name and API key are required.")

    return _system_default_model()
