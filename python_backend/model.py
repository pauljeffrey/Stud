from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.openai import OpenAIModel, OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider

from dotenv import load_dotenv
import logging
import os

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
)

_DEFAULT_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"


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
        model = GeminiModel(
            MODEL_NAME, provider=GoogleGLAProvider(api_key=GOOGLE_API_KEY)
        )
    elif 'claude' in MODEL_NAME_LOWER:
        model = AnthropicModel(
            MODEL_NAME, provider=AnthropicProvider(api_key=API_KEY)
        )
    elif 'gpt' in MODEL_NAME_LOWER or 'openai' in MODEL_NAME_LOWER:
        model = OpenAIModel(
            MODEL_NAME, provider=OpenAIProvider(api_key=OPENAI_API_KEY)
        )
    else:
        # Unknown name — route through OpenRouter as a safe fallback
        model = OpenRouterModel(
            MODEL_NAME,
            provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
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


def select_model_with_fallback(user_model_name: str | None, user_api_key: str | None):
    """Try the user-supplied model/key; fall back to the system default on any error.

    This is the preferred entry point for agents that accept per-user model
    configuration.  If the user's model initialises fine but fails at inference
    time the calling agent should catch the exception and retry with
    ``_system_default_model()``.

    Returns:
        tuple: (model, agent)
    """
    if user_model_name and user_api_key:
        try:
            return select_model(user_model_name, user_api_key)
        except Exception as exc:
            logger.warning(
                "User model '%s' failed to initialise (%s) — falling back to system default.",
                user_model_name,
                exc,
            )
    return _system_default_model()
