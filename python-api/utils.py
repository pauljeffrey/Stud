from game_config import *
import random
from prompts.game_init_prompt import PROMPT_TEMPLATE
from models import GameScenario
from transformers import pipeline  # Assuming we're using a Hugging Face model

# Function to Select Random Attributes
def get_random_attributes():
    return {
        "nation": random.choice(NATIONS),
        "economic_advantage": random.choice(ECONOMIC_ADVANTAGES),
        "profession": random.choice(PROFESSIONS),
        "era": random.choice(ERAS),
        "continent": random.choice(CONTINENTS),
        "natural_condition": random.choice(NATURAL_CONDITIONS),
        "mode": random.choice(MODES),
        "area": random.choice(AREAS),
    }
    

# Function to Generate Game Scenario Using AI
def generate_game_scenario():
    attributes = get_random_attributes()
    prompt = PROMPT_TEMPLATE['game_scenario_init'].format(**attributes)

    # Assuming we're using a Hugging Face pipeline for text generation
    generator = pipeline("text-generation", model="huggingface/Gemini")  # Replace with actual AI model
    response = generator(prompt, max_length=500)[0]['generated_text']

    # Extract information from response (Assuming AI generates structured output)
    scenario_lines = response.split("\n")
    return GameScenario(
        game_scenario=scenario_lines[0], 
        country_situation=scenario_lines[1], 
        metadata={"attributes": attributes},
        objective=scenario_lines[-1]  # Assuming last line contains the objective
    )

