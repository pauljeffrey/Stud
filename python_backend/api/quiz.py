"""
Enhanced Quiz API endpoints for Stud
Uses enhanced quiz agent with internet access and open-ended question support
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional, Dict, Any
import os
from quiz_agent_enhanced import generate_quiz, score_open_ended_answer
from supabase import create_client, Client
from config import config

router = APIRouter()

# Initialize Supabase client
supabase: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_SERVICE_ROLE_KEY
)


@router.post("/quiz/generate")
async def create_quiz(request: Dict[str, Any]):
    """
    Generate a new quiz with enhanced features
    
    Request body:
    - quiz_type: str
    - num_questions: int
    - num_multiple_choice: Optional[int]
    - num_open_ended: Optional[int]
    - time_limit: int
    - source: "ai_knowledge" | "document"
    - document_id: Optional[str]
    - model_name: Optional[str]
    - api_key: Optional[str]
    - provider: "google" | "openai"
    - use_internet: bool (default True)
    """
    try:
        quiz_type = request.get("quiz_type", "general")
        num_questions = request.get("num_questions", 10)
        num_multiple_choice = request.get("num_multiple_choice")
        num_open_ended = request.get("num_open_ended")
        time_limit = request.get("time_limit", 300)
        source = request.get("source", "ai_knowledge")
        document_id = request.get("document_id")
        model_name = request.get("model_name")
        api_key = request.get("api_key")
        provider = request.get("provider", "google")
        use_internet = request.get("use_internet", True)

        # Get document content if source is document
        context = None
        if source == "document" and document_id:
            doc_result = supabase.table("documents").select("content").eq("id", document_id).execute()
            if doc_result.data:
                context = doc_result.data[0].get("content", "")

        # Generate quiz using enhanced agent
        quiz = await generate_quiz(
            quiz_type=quiz_type,
            num_questions=num_questions,
            time_limit=time_limit,
            context=context,
            source=source,
            num_multiple_choice=num_multiple_choice,
            num_open_ended=num_open_ended,
            model_name=model_name,
            api_key=api_key,
            provider=provider,
            use_internet=use_internet
        )

        # Save quiz to database
        quiz_data = quiz.model_dump(mode="json")
        supabase.table("quizzes").insert({
            "id": quiz.id,
            "user_id": "user_123",  # TODO: Get from auth
            "title": quiz.title,
            "quiz_type": quiz_type,
            "source": source,
            "document_id": document_id,
            "questions": quiz_data["questions"],
            "time_limit": time_limit,
            "total_questions": quiz.totalQuestions
        }).execute()

        return quiz_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@router.post("/quiz/submit")
async def submit_quiz(request: Dict[str, Any]):
    """
    Submit quiz answers and calculate scores
    
    Request body:
    - quiz_id: str
    - answers: Dict[str, str] (question_id -> answer)
    - scores: Optional[Dict[str, float]] (pre-calculated scores)
    - total_score: Optional[float]
    - time_spent: int
    """
    try:
        quiz_id = request.get("quiz_id")
        answers = request.get("answers", {})
        scores = request.get("scores", {})
        total_score = request.get("total_score", 0)
        time_spent = request.get("time_spent", 0)

        # Save quiz result
        result_data = {
            "quiz_id": quiz_id,
            "user_id": "user_123",  # TODO: Get from auth
            "answers": answers,
            "scores": scores,
            "total_score": total_score,
            "time_spent": time_spent
        }

        supabase.table("quiz_results").insert(result_data).execute()

        return {
            "success": True,
            "message": "Quiz submitted successfully",
            "total_score": total_score
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")


@router.post("/quiz/score-open")
async def score_open_ended(request: Dict[str, Any]):
    """
    Score an open-ended quiz answer using AI
    
    Request body:
    - question: str
    - correct_answer: str
    - user_answer: str
    - model_name: Optional[str]
    - api_key: Optional[str]
    - provider: "google" | "openai"
    """
    try:
        from quiz_agent_enhanced import QuizQuestion

        question = QuizQuestion(
            question=request.get("question"),
            type="open_ended",
            correct_answer=request.get("correct_answer"),
            explanation=""
        )

        score_result = await score_open_ended_answer(
            question=question,
            user_answer=request.get("user_answer"),
            model_name=request.get("model_name"),
            api_key=request.get("api_key"),
            provider=request.get("provider", "google")
        )

        return score_result.model_dump(mode="json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to score answer: {str(e)}")
