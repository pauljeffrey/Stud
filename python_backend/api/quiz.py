"""
Enhanced Quiz API endpoints for Stud
Uses enhanced quiz agent with internet access and open-ended question support
"""
import asyncio
import logging
from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, Any
from agents.quiz_agent import get_quiz_agent
from models.states import QuizQuestion, DifficultyLevel
from models.api_requests import ScoreOpenAnswerRequest
from service.redis_service import get_redis_service
from service.database import get_database_service
from api.auth_deps import resolve_user_id

logger = logging.getLogger(__name__)
router = APIRouter()


async def _generate_document_quiz_and_notify(
    *,
    quiz_agent,
    document_id: str,
    topic: str,
    user_id: str,
    quiz_type: str,
    num_questions: int,
    time_limit: int,
    num_multiple_choice: Optional[int],
    num_true_false: Optional[int],
    num_open_ended: Optional[int],
    difficulty_level,
    context: Optional[str],
    user_subject_of_study: Optional[str],
    user_profession: Optional[str],
) -> None:
    """Background job: generate a topic-focused quiz from a (usually central
    library) document, then notify the user so they don't have to wait on the
    multi-query retrieval + generation pipeline."""
    db_service = get_database_service()
    try:
        quiz = await quiz_agent.generate_quiz(
            from_document=True,
            document_id=document_id,
            topic=topic,
            user_id=user_id,
            num_questions=num_questions,
            quiz_type=quiz_type,
            user_subject_of_study=user_subject_of_study,
            user_profession=user_profession,
            time_limit=time_limit,
            context=context,
            num_multiple_choice=num_multiple_choice,
            num_true_false=num_true_false,
            num_open_ended=num_open_ended,
            difficulty_level=difficulty_level,
        )
        quiz_data = quiz.model_dump(mode="json")
        created = await db_service.create_quiz(
            user_id=user_id,
            title=quiz.title,
            questions=quiz_data["questions"],
            quiz_type=quiz_type,
            time_limit=time_limit,
            total_questions=quiz.totalQuestions,
            source="document",
            document_id=document_id,
        )
        await db_service.create_notification(
            user_id=user_id,
            type="quiz_ready",
            title="Quiz ready",
            message=f"Your quiz on '{topic}' is ready.",
            related_id=created.get("id") or quiz.id,
        )
    except Exception as e:
        logger.exception(f"Background topic-focused quiz generation failed for document {document_id}")
        await db_service.create_notification(
            user_id=user_id,
            type="quiz_failed",
            title="Quiz generation failed",
            message=f"We couldn't generate a quiz on '{topic}': {str(e)[:200]}.",
        )


@router.post("/quiz/generate")
async def create_quiz(
    request: Dict[str, Any],
    authorization: Optional[str] = Header(None),
):
    """
    Generate a new quiz with enhanced features
    
    Request body:
    - quiz_type: str
    - num_questions: int
    - num_multiple_choice: Optional[int]
    - num_true_false: Optional[int]
    - num_open_ended: Optional[int]
    - time_limit: int
    - source: "ai_knowledge" | "document"
    - document_id: Optional[str]
    - user_subject_of_study: Optional[str]
    - difficulty_level: Optional[str]
    - model_name: Optional[str]
    - api_key: Optional[str]
    - provider: "google" | "openai"
    - use_internet: bool (default True)
    """
    try:
        from models.states import DifficultyLevel
        
        quiz_type = request.get("quiz_type", "general")
        num_questions = request.get("num_questions", 10)
        num_multiple_choice = request.get("num_multiple_choice")
        num_true_false = request.get("num_true_false")
        num_open_ended = request.get("num_open_ended")
        time_limit = request.get("time_limit", 300)
        source = request.get("source", "ai_knowledge")
        document_id = request.get("document_id")
        file_path = request.get("file_path")
        raw_uid = request.get("user_id")
        body_uid = raw_uid.strip() if raw_uid and str(raw_uid).strip() else None
        user_id = resolve_user_id(authorization, body_uid)
        user_subject_of_study = request.get("user_subject_of_study")
        user_profession = request.get("user_profession")
        difficulty_level_str = request.get("difficulty_level")
        db_service = get_database_service()
        if not user_subject_of_study or not user_profession:
            user = await db_service.get_user(user_id)
            if user:
                user_profession = user_profession or user.get("profession")
                user_subject_of_study = user_subject_of_study or user_profession
        user_subject_of_study = user_subject_of_study or user_profession or "general medicine"
        model_name = request.get("model_name")
        api_key = request.get("api_key")
        provider = request.get("provider", "google")
        use_internet = request.get("use_internet", True)

        # Parse difficulty level
        difficulty_level = None
        if difficulty_level_str:
            try:
                difficulty_level = DifficultyLevel(difficulty_level_str)
            except:
                difficulty_level = DifficultyLevel.Medium

        # Get document content if source is document (for context and fallback when vector DB expired)
        context = None
        doc_content_fallback = None
        if source == "document" and document_id:
            try:
                doc = await db_service.get_document(document_id)
                if doc:
                    context = doc.get("content", "")
                    doc_content_fallback = context
            except Exception as e:
                logger.warning(f"Error fetching document: {e}")

        topic = request.get("topic")
        if topic and source == "document" and document_id:
            asyncio.create_task(
                _generate_document_quiz_and_notify(
                    quiz_agent=get_quiz_agent(model_name, api_key, provider, use_internet),
                    document_id=document_id,
                    topic=topic,
                    user_id=user_id,
                    quiz_type=quiz_type,
                    num_questions=num_questions,
                    time_limit=time_limit,
                    num_multiple_choice=num_multiple_choice,
                    num_true_false=num_true_false,
                    num_open_ended=num_open_ended,
                    difficulty_level=difficulty_level,
                    context=context,
                    user_subject_of_study=user_subject_of_study,
                    user_profession=user_profession,
                )
            )
            return {
                "success": True,
                "status": "queued",
                "message": f"Generating your quiz on '{topic}' — we'll notify you when it's ready.",
            }

        # Generate quiz using agent
        quiz_agent = get_quiz_agent(model_name, api_key, provider, use_internet)
        try:
            quiz = await quiz_agent.generate_quiz(
                from_document=(source == "document"),
                document_id=document_id,
                file_path=file_path,
                user_id=user_id,
                num_questions=num_questions,
                quiz_type=quiz_type,
                user_subject_of_study=user_subject_of_study,
                user_profession=user_profession,
                time_limit=time_limit,
                context=context,
                num_multiple_choice=num_multiple_choice,
                num_true_false=num_true_false,
                num_open_ended=num_open_ended,
                difficulty_level=difficulty_level
            )
        except (ValueError, Exception) as doc_err:
            # Fallback when vector DB expired and reingest fails: use stored content
            err_msg = str(doc_err).lower()
            if source == "document" and document_id and ("expired" in err_msg or "not found" in err_msg or "re-ingest" in err_msg) and doc_content_fallback and len(doc_content_fallback or "") > 200:
                quiz = await quiz_agent.generate_quiz(
                    from_document=True,
                    document_id=None,
                    text_content=doc_content_fallback,
                    user_id=user_id,
                    num_questions=num_questions,
                    quiz_type=quiz_type,
                    user_subject_of_study=user_subject_of_study,
                    user_profession=user_profession,
                    time_limit=time_limit,
                    context=context,
                    num_multiple_choice=num_multiple_choice,
                    num_true_false=num_true_false,
                    num_open_ended=num_open_ended,
                    difficulty_level=difficulty_level
                )
            else:
                raise

        # Save quiz to database
        try:
            quiz_data = quiz.model_dump(mode="json")
            await db_service.create_quiz(
                user_id=user_id,
                title=quiz.title,
                questions=quiz_data["questions"],
                quiz_type=quiz_type,
                time_limit=time_limit,
                total_questions=quiz.totalQuestions,
                source=source,
                document_id=document_id
            )
        except Exception as e:
            logger.warning(f"Error saving quiz to DB: {e}")

        # Cache quiz in Redis
        try:
            redis_service = await get_redis_service()
            await redis_service.cache_quiz_session(
                quiz_id=quiz.id,
                quiz_data=quiz_data,
                ttl=3600  # 1 hour
            )
        except Exception as e:
            logger.warning(f"Error caching quiz in Redis: {e}")

        return quiz_data

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate quiz")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")


@router.post("/quiz/submit")
async def submit_quiz(
    request: Dict[str, Any],
    authorization: Optional[str] = Header(None),
):
    """
    Submit quiz answers and calculate scores
    
    Request body:
    - quiz_id: str
    - answers: Dict[str, str] (question_id -> answer)
    - scores: Optional[Dict[str, float]] (pre-calculated scores)
    - total_score: Optional[float]
    - time_spent: int
    - user_id: Optional[str]
    """
    try:
        from service.redis_service import get_redis_service
        from service.database import get_database_service
        
        quiz_id = request.get("quiz_id")
        answers = request.get("answers", {})
        scores = request.get("scores", {})
        total_score = request.get("total_score", 0)
        time_spent = request.get("time_spent", 0)
        raw_uid = request.get("user_id")
        body_uid = raw_uid.strip() if raw_uid and str(raw_uid).strip() else None
        user_id = resolve_user_id(authorization, body_uid)

        # Save quiz result to database
        try:
            db_service = get_database_service()
            await db_service.create_quiz_result(
                user_id=user_id,
                quiz_id=quiz_id,
                answers=answers,
                scores=scores,
                total_score=total_score,
                time_spent=time_spent
            )
            # total_score is on a 0-10 scale (average of per-question 0-10 scores);
            # convert to a 0-100 percentage for XP/statistics.
            score_pct = min(100.0, max(0.0, float(total_score or 0) * 10))
            if user_id and not str(user_id).startswith("demo_"):
                try:
                    xp = int(10 + (score_pct / 100) * 40)
                    await db_service.add_experience_points(
                        user_id=user_id,
                        xp_amount=xp,
                        total_quizzes_delta=1
                    )
                except Exception as xp_err:
                    logger.warning(f"Error awarding quiz XP: {xp_err}")
                try:
                    await db_service.record_quiz_stat(
                        user_id=user_id,
                        taken=1,
                        passed=1 if score_pct >= 70 else 0,
                        score_pct=score_pct,
                        time_spent=time_spent,
                    )
                except Exception as stat_err:
                    logger.warning(f"Error recording quiz statistics: {stat_err}")
        except Exception as e:
            logger.warning(f"Error saving quiz result to DB: {e}")

        # Cache quiz progress in Redis (for resume capability)
        try:
            redis_service = await get_redis_service()
            await redis_service.cache_quiz_progress(
                user_id=user_id,
                quiz_id=quiz_id,
                answers=answers,
                current_question=len(answers),
                time_remaining=max(0, request.get("time_limit", 600) - time_spent),
                ttl=3600
            )
        except Exception as e:
            logger.warning(f"Error caching quiz progress in Redis: {e}")

        return {
            "success": True,
            "message": "Quiz submitted successfully",
            "total_score": total_score
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to submit quiz")
        raise HTTPException(status_code=500, detail="Failed to submit quiz")


@router.get("/quiz/saved")
async def list_saved_quizzes(authorization: Optional[str] = Header(None)):
    """List the current user's saved quizzes, enriched with their own result history."""
    user_id = resolve_user_id(authorization, None)
    db_service = get_database_service()
    client = db_service.client
    try:
        rows = await db_service.list_saved_quizzes(user_id)
        quiz_ids = [r["quiz_id"] for r in rows if r.get("quiz_id")]

        results_by_quiz: Dict[str, list] = {}
        if quiz_ids:
            try:
                result_rows = await asyncio.to_thread(
                    lambda: client.table("quiz_results")
                    .select("quiz_id, total_score, completed_at")
                    .eq("user_id", user_id)
                    .in_("quiz_id", quiz_ids)
                    .order("completed_at", desc=True)
                    .execute().data or []
                )
                for rr in result_rows:
                    results_by_quiz.setdefault(rr["quiz_id"], []).append(rr)
            except Exception:
                logger.warning("Failed to fetch quiz result history for saved quizzes")

        quizzes = []
        for row in rows:
            quiz = row.get("quizzes") or {}
            quiz_id = row.get("quiz_id")
            history = results_by_quiz.get(quiz_id, [])
            best_score = max((float(h.get("total_score") or 0) for h in history), default=None)
            quizzes.append({
                "id": row.get("id"),
                "quizId": quiz_id,
                "title": quiz.get("title", "Untitled Quiz"),
                "quizType": quiz.get("quiz_type", "general"),
                "totalQuestions": quiz.get("total_questions", 0),
                "timeLimit": quiz.get("time_limit", 0),
                "difficulty": quiz.get("difficulty", "intermediate"),
                "savedAt": row.get("saved_at"),
                "lastTaken": history[0].get("completed_at") if history else None,
                "bestScore": round(best_score * 10) if best_score is not None else None,
                "timesTaken": len(history),
            })
        return {"success": True, "quizzes": quizzes}
    except Exception:
        logger.exception("Failed to list saved quizzes")
        raise HTTPException(status_code=500, detail="Failed to list saved quizzes")


@router.post("/quiz/saved")
async def save_quiz(request: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """Save a quiz to the current user's saved list."""
    quiz_id = request.get("quiz_id")
    if not quiz_id:
        raise HTTPException(status_code=400, detail="quiz_id is required")
    user_id = resolve_user_id(authorization, request.get("user_id"))
    try:
        db_service = get_database_service()
        await db_service.save_quiz_for_user(user_id, quiz_id)
        return {"success": True}
    except Exception:
        logger.exception("Failed to save quiz")
        raise HTTPException(status_code=500, detail="Failed to save quiz")


@router.delete("/quiz/saved/{quiz_id}")
async def unsave_quiz(quiz_id: str, authorization: Optional[str] = Header(None)):
    """Remove a quiz from the current user's saved list."""
    user_id = resolve_user_id(authorization, None)
    try:
        db_service = get_database_service()
        await db_service.unsave_quiz_for_user(user_id, quiz_id)
        return {"success": True}
    except Exception:
        logger.exception("Failed to remove saved quiz")
        raise HTTPException(status_code=500, detail="Failed to remove saved quiz")


@router.post("/quiz/score-open")
async def score_open_ended(request: ScoreOpenAnswerRequest):
    """Score an open-ended quiz answer using AI."""
    try:
        question = QuizQuestion(
            question=request.question,
            type="open_ended",
            correct_answer=request.correct_answer,
            explanation=request.explanation or "",
            difficulty_level=DifficultyLevel.Medium,
        )

        quiz_agent = get_quiz_agent(
            model_name=request.model_name,
            api_key=request.api_key,
            provider=request.provider or "google",
        )

        score_result = await quiz_agent.score_open_ended_answer(
            question=question,
            user_answer=request.user_answer,
            model_name=request.model_name,
            api_key=request.api_key,
            provider=request.provider or "google",
        )

        return score_result.model_dump(mode="json")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to score answer")
        raise HTTPException(status_code=500, detail="Failed to score answer")


# NOTE: this must stay registered after the more specific /quiz/saved* routes
# above — FastAPI matches path routes in registration order, and "saved"
# would otherwise match this {quiz_id} pattern first.
@router.get("/quiz/{quiz_id}")
async def get_quiz(quiz_id: str):
    """Fetch a previously-generated quiz by id (e.g. to retake a saved quiz)."""
    try:
        db_service = get_database_service()
        quiz = await db_service.get_quiz(quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        questions = quiz.get("questions")
        if isinstance(questions, str):
            import json
            questions = json.loads(questions)
        return {
            "id": quiz.get("id"),
            "title": quiz.get("title", "Untitled Quiz"),
            "questions": questions or [],
            "timeLimit": quiz.get("time_limit", 0),
            "totalQuestions": quiz.get("total_questions", 0),
            "source": quiz.get("source", "ai_knowledge"),
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch quiz")
        raise HTTPException(status_code=500, detail="Failed to fetch quiz")
