"""
Enhanced Quiz Agent for Stud
Includes internet access tool for current information
Supports both multiple choice and open-ended questions
"""
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import uuid
import httpx
from datetime import datetime

from config import config
from agents.base_agent import BaseAgent
from agents.agents import select_model


class QuizQuestion(BaseModel):
    question: str
    type: str  # "multiple_choice" or "open_ended"
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str
    question_id: Optional[str] = None


class Quiz(BaseModel):
    id: str
    title: str
    questions: List[QuizQuestion]
    timeLimit: int
    totalQuestions: int
    source: str  # "ai_knowledge" or "document"


class OpenEndedAnswer(BaseModel):
    """Model for scoring open-ended answers"""
    score: float  # 0-10
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    correct_elements: List[str]
    missing_elements: List[str]


async def search_internet(query: str, api_key: Optional[str] = None) -> str:
    """
    Search the internet for current information
    Uses Serper API if available, otherwise falls back to basic search
    """
    serper_api_key = api_key or config.SERPER_API_KEY
    
    if not serper_api_key:
        # Fallback: return empty (agent will use its knowledge)
        return ""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": serper_api_key,
                    "Content-Type": "application/json"
                },
                json={"q": query},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract relevant information
                results = []
                if "organic" in data:
                    for item in data["organic"][:5]:  # Top 5 results
                        results.append(f"{item.get('title', '')}: {item.get('snippet', '')}")
                
                return "\n".join(results)
    except Exception as e:
        print(f"Internet search error: {str(e)}")
    
    return ""


class QuizAgent(BaseAgent):
    """
    Quiz Agent for creating medical quiz questions
    Supports both multiple choice and open-ended questions with optional internet access
    """
    
    def __init__(
        self, 
        model_name: Optional[str] = None, 
        api_key: Optional[str] = None, 
        provider: str = "google",
        use_internet: bool = True
    ):
        """
        Initialize the Quiz Agent
        
        Args:
            model_name: Model name
            api_key: API key
            provider: "google" or "openai"
            use_internet: Whether to enable internet search
        """
        super().__init__(model_name, api_key, provider)
        self.use_internet = use_internet
        
        # Initialize agent using the pattern from agents.py
        model_name = model_name or config.QUIZ_MODEL_NAME or "gemini-2.5-pro"
        api_key = api_key or config.API_KEY
        model = select_model(model_name, api_key)
        
        system_prompt = """
        You are a medical education expert creating quiz questions.
        Generate high-quality, medically accurate questions that test understanding of medical concepts.
        
        For multiple choice questions, provide 4 options with only one correct answer.
        For open-ended questions, ask questions that require detailed explanations.
        
        Always provide clear explanations for the correct answers.
        Focus on practical medical knowledge that would be useful for healthcare professionals.
        """
        
        if use_internet:
            system_prompt += """
        
        You have access to internet search for current information. Use it when:
        - Questions require recent medical guidelines or protocols
        - Current treatment recommendations are needed
        - Latest research findings are relevant
        """
            self.agent = Agent(
                model,
                system_prompt=system_prompt,
                output_type=Quiz,
                tools=[search_internet]
            )
        else:
            self.agent = Agent(
                model,
                system_prompt=system_prompt,
                output_type=Quiz
            )
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize the model"""
        super()._reinitialize_model(model_name, api_key)
        model = select_model(self.model_name or config.QUIZ_MODEL_NAME or "gemini-2.5-pro", self.api_key or config.API_KEY)
        
        system_prompt = """
        You are a medical education expert creating quiz questions.
        Generate high-quality, medically accurate questions that test understanding of medical concepts.
        
        For multiple choice questions, provide 4 options with only one correct answer.
        For open-ended questions, ask questions that require detailed explanations.
        
        Always provide clear explanations for the correct answers.
        Focus on practical medical knowledge that would be useful for healthcare professionals.
        """
        
        if self.use_internet:
            system_prompt += """
        
        You have access to internet search for current information. Use it when:
        - Questions require recent medical guidelines or protocols
        - Current treatment recommendations are needed
        - Latest research findings are relevant
        """
            self.agent = Agent(
                model,
                system_prompt=system_prompt,
                output_type=Quiz,
                tools=[search_internet]
            )
        else:
            self.agent = Agent(
                model,
                system_prompt=system_prompt,
                output_type=Quiz
            )


# Global instance
_quiz_agent_instance: Optional[QuizAgent] = None


def get_quiz_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google",
    use_internet: bool = True
) -> QuizAgent:
    """Get or create the global Quiz Agent instance"""
    global _quiz_agent_instance
    if _quiz_agent_instance is None:
        _quiz_agent_instance = QuizAgent(model_name, api_key, provider, use_internet)
    return _quiz_agent_instance


async def generate_quiz(
    quiz_type: str,
    num_questions: int,
    time_limit: int,
    context: Optional[str] = None,
    source: str = "ai_knowledge",
    num_multiple_choice: Optional[int] = None,
    num_open_ended: Optional[int] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google",
    use_internet: bool = True
) -> Quiz:
    """
    Generate a medical quiz using AI (uses QuizAgent class)
    """
    quiz_agent_instance = get_quiz_agent(model_name, api_key, provider, use_internet)
    quiz_agent = quiz_agent_instance.agent
    
    # Determine question distribution
    if num_multiple_choice is None and num_open_ended is None:
        # Default: 70% multiple choice, 30% open-ended
        num_multiple_choice = int(num_questions * 0.7)
        num_open_ended = num_questions - num_multiple_choice
    elif num_multiple_choice is None:
        num_multiple_choice = num_questions - (num_open_ended or 0)
    elif num_open_ended is None:
        num_open_ended = num_questions - num_multiple_choice
    
    context_prompt = f"Context: {context}\n\n" if context else ""
    
    prompt = f"""
    {context_prompt}Generate a medical quiz with the following specifications:
    - Type: {quiz_type}
    - Total Questions: {num_questions}
      - Multiple Choice: {num_multiple_choice}
      - Open-ended (Theory): {num_open_ended}
    - Time limit: {time_limit} seconds per question
    - Source: {source}
    - Focus on medical knowledge appropriate for healthcare professionals
    
    For multiple choice questions:
    - Provide exactly 4 options
    - Only one correct answer
    - Include clear explanations
    
    For open-ended questions:
    - Require detailed explanations
    - Test critical thinking and application
    - Include model answers for scoring
    
    Create engaging, educational questions that test both theoretical knowledge and practical application.
    """
    
    result = await quiz_agent.run(prompt)
    
    # Ensure the quiz has the correct structure
    quiz = result.output
    quiz.id = f"quiz_{uuid.uuid4()}"
    quiz.timeLimit = time_limit
    quiz.totalQuestions = len(quiz.questions)
    quiz.source = source
    
    # Assign IDs to questions
    for i, question in enumerate(quiz.questions):
        if not question.question_id:
            question.question_id = f"q_{i+1}_{uuid.uuid4()}"
    
    return quiz


async def score_open_ended_answer(
    question: QuizQuestion,
    user_answer: str,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google"
) -> OpenEndedAnswer:
    """
    Score an open-ended answer using AI
    
    Args:
        question: The quiz question
        user_answer: User's answer
        model_name: Optional model name
        api_key: Optional API key
        provider: "google" or "openai"
    """
    model = select_model(model_name or "gemini-2.0-flash-exp", api_key or config.API_KEY)
    
    scoring_agent = Agent(
        model,
        system_prompt="""
        You are a medical education evaluator. Score open-ended quiz answers on a scale of 0-10.
        Provide detailed feedback, identify strengths and weaknesses, and list correct/missing elements.
        """,
        output_type=OpenEndedAnswer
    )
    
    prompt = f"""
    Evaluate this open-ended quiz answer:
    
    Question: {question.question}
    Correct Answer/Model Answer: {question.correct_answer}
    User Answer: {user_answer}
    Explanation: {question.explanation}
    
    Score the answer (0-10) and provide:
    1. Overall score
    2. Detailed feedback
    3. List of strengths
    4. List of weaknesses
    5. Correct elements mentioned
    6. Missing elements
    
    Be fair but thorough. Reward partial understanding and penalize significant errors.
    """
    
    result = await scoring_agent.run(prompt)
    return result.output
