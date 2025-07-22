from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import uuid

class QuizQuestion(BaseModel):
    id: str
    question: str
    type: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str

class Quiz(BaseModel):
    id: str
    title: str
    questions: List[QuizQuestion]
    timeLimit: int
    totalQuestions: int

def get_quiz_agent(model_name: str = None, api_key: str = None):
    model_name = model_name or os.getenv("MODEL_NAME", "gemini-2.0-flash")
    api_key = api_key or os.getenv("MODEL_API_KEY")
    
    return Agent(
        GeminiModel(model_name, provider=GoogleGLAProvider(api_key=api_key)),
        system_prompt="""
        You are a medical education expert creating quiz questions.
        Generate high-quality, medically accurate questions that test understanding of medical concepts.
        
        For multiple choice questions, provide 4 options with only one correct answer.
        For true/false questions, create statements that test specific medical knowledge.
        For open-ended questions, ask questions that require detailed explanations.
        
        Always provide clear explanations for the correct answers.
        Focus on practical medical knowledge that would be useful for healthcare professionals.
        """,
        output_type=Quiz
    )

async def generate_quiz(
    quiz_type: str,
    num_questions: int,
    time_limit: int,
    context: str = None
) -> Quiz:
    """Generate a medical quiz using AI"""
    
    quiz_agent = get_quiz_agent()
    
    context_prompt = f"Context: {context}\n\n" if context else ""
    
    prompt = f"""
    {context_prompt}Generate a medical quiz with the following specifications:
    - Type: {quiz_type}
    - Number of questions: {num_questions}
    - Time limit: {time_limit} seconds
    - Focus on medical knowledge appropriate for healthcare professionals
    
    Create engaging, educational questions that test both theoretical knowledge and practical application.
    """
    
    result = await quiz_agent.run(prompt)
    
    # Ensure the quiz has the correct structure
    quiz = result.output
    quiz.id = f"quiz_{uuid.uuid4()}"
    quiz.timeLimit = time_limit
    quiz.totalQuestions = len(quiz.questions)
    
    # Assign IDs to questions if not present
    for i, question in enumerate(quiz.questions):
        if not question.id:
            question.id = f"q_{i+1}_{uuid.uuid4()}"
    
    return quiz
