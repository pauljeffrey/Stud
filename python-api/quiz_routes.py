from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
import os
from quiz_agent import generate_quiz
from supabase import create_client

router = APIRouter()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

@router.post("/api/quiz/generate")
async def create_quiz(
    quiz_type: str = Form(...),
    num_questions: int = Form(...),
    time_limit: int = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """Generate a new quiz"""
    try:
        context = None
        
        # If file is uploaded, extract context
        if file:
            content = await file.read()
            if file.content_type == 'text/plain':
                context = content.decode('utf-8')
            else:
                # For other file types, you'd implement proper text extraction
                context = f"Content from uploaded file: {file.filename}"
        
        # Generate quiz using AI
        quiz = await generate_quiz(quiz_type, num_questions, time_limit, context)
        
        # Save quiz to database
        quiz_data = quiz.dict()
        result = supabase.table("quizzes").insert(quiz_data).execute()
        
        return quiz_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

@router.post("/api/quiz/submit")
async def submit_quiz(request: dict):
    """Submit quiz answers and calculate score"""
    try:
        quiz_id = request.get("quizId")
        answers = request.get("answers", {})
        score = request.get("score", 0)
        time_spent = request.get("timeSpent", 0)
        
        # Save quiz result
        result_data = {
            "quiz_id": quiz_id,
            "user_id": "user_123",  # In production, get from authentication
            "answers": answers,
            "score": score,
            "time_spent": time_spent,
            "completed_at": "now()"
        }
        
        result = supabase.table("quiz_results").insert(result_data).execute()
        
        return {"success": True, "message": "Quiz submitted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")
