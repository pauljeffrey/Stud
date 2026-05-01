from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from dotenv import load_dotenv
import os

load_dotenv()


MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("MODEL_API_KEY")



def select_model(MODEL_NAME, API_KEY):
    """
    Select and initialize a model based on model name and API key
    
    Args:
        MODEL_NAME: Name of the model (e.g., 'gemini-2.0-flash', 'gpt-4o', 'claude-3-5-sonnet-latest')
        API_KEY: API key for the model provider
        
    Returns:
        tuple: (model, agent)
    """
    if not MODEL_NAME:
        MODEL_NAME = "gemini-2.0-flash"  # Default fallback
    
    MODEL_NAME_LOWER = MODEL_NAME.lower()
    
    if 'gemini' in MODEL_NAME_LOWER:
        model = GeminiModel(
            MODEL_NAME, provider=GoogleGLAProvider(api_key=API_KEY)
        )
    elif 'claude' in MODEL_NAME_LOWER:
        model = AnthropicModel(
            MODEL_NAME, provider=AnthropicProvider(api_key=API_KEY)
        )
    elif 'gpt' in MODEL_NAME_LOWER or 'openai' in MODEL_NAME_LOWER:
        model = OpenAIModel(
            MODEL_NAME, provider=OpenAIProvider(api_key=API_KEY)
        )
    else:
        # Default to Gemini if model type not recognized
        model = GeminiModel(
            MODEL_NAME or "gemini-2.0-flash", 
            provider=GoogleGLAProvider(api_key=API_KEY)
        )
    
    agent = Agent(model)
    
    return model, agent
