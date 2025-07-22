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
    if 'gemini' in MODEL_NAME:
        model = GeminiModel(
            MODEL_NAME, provider=GoogleGLAProvider(api_key=API_KEY)
        )
    elif 'claude' in MODEL_NAME:
        model = AnthropicModel(
            'claude-3-5-sonnet-latest', provider=AnthropicProvider(api_key='your-api-key')
        )
    elif 'gpt' in MODEL_NAME:
        model = OpenAIModel(
            'gpt-4o', provider=OpenAIProvider(api_key='your-api-key')
            )
    else:
        pass
    agent = Agent(model)
    
    return model, agent
