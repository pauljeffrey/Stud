"""
Learning API endpoints
Handles document upload, processing, and RAG-based chat
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, Header, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import hashlib
import json
import asyncio
from datetime import datetime
import uuid
import logging

from schema import LearningChatRequest
from service.document_processor import get_document_processor
from service.document_game_session import save_mediquest_session
from service.database import get_database_service
from agents.tutor_agent import get_tutor_agent
from utils import get_chat_history_from_storage
from api.auth_deps import (
    get_current_user_id,
    resolve_user_id,
    resolve_user_id_or_query,
)
from api.rate_limit import enforce_rate_limit
from configs.config import config
from http_constants import SSE_STREAM_HEADERS

logger = logging.getLogger(__name__)

router = APIRouter()

# Services initialised lazily so a broken AI model config does not crash the
# entire app (and auth) at startup — they are instantiated on first use.
doc_processor = get_document_processor()
db_service = get_database_service()

_tutor_agent = None


def _get_tutor_agent():
    global _tutor_agent
    if _tutor_agent is None:
        _tutor_agent = get_tutor_agent()
    return _tutor_agent


@router.get("/learning/enrollments")
async def list_learning_enrollments(
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """List learning journeys (enrollments). JWT sets user; else user_id query (dev)."""
    try:
        uid = resolve_user_id_or_query(authorization, user_id)
        rows = await db_service.list_user_enrollments(uid, limit=50)
        return {"success": True, "enrollments": rows}
    except Exception as e:
        logger.error(f"List enrollments error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list enrollments")


def _serialize_document(d: dict) -> dict:
    return {
        "id": d["id"],
        "file_name": d.get("file_name", d.get("name", "Untitled")),
        "processed": d.get("processed", False),
        "processing_status": d.get("processing_status", "pending"),
        "scope": d.get("scope", "private"),
        "pinecone_index_name": d.get("pinecone_index_name"),
        "pinecone_index_expires_at": d.get("pinecone_index_expires_at"),
        "chunk_count": d.get("chunk_count", 0),
    }


@router.get("/learning/documents")
async def list_documents(user_id: str = Depends(get_current_user_id)):
    """
    List the caller's own uploaded documents (file_name, id, expiry/processing
    status). Used by quiz page when source is 'from document', and by the
    Study page's own-document list. See /learning/documents/library for the
    shared central-library documents.
    """
    try:
        docs = await db_service.get_user_documents(user_id, limit=50)
        return {"success": True, "documents": [_serialize_document(d) for d in docs]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.get("/learning/documents/library")
async def list_library_documents():
    """
    The shared central library: curated, standard reference documents
    available to every user (no auth required to browse — matches other
    public read endpoints). Encourage checking here before uploading a
    private copy, to avoid duplicate vectorization of the same material.
    """
    try:
        docs = await db_service.list_global_documents()
        return {"success": True, "documents": [_serialize_document(d) for d in docs]}
    except Exception as e:
        logger.error(f"List library documents error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list central library documents")


@router.post("/learning/documents/{document_id}/suggest-global")
async def suggest_document_for_library(
    document_id: str,
    request: Optional[dict] = None,
    user_id: str = Depends(get_current_user_id),
):
    """File a request to promote the caller's own document into the shared
    central library. Reviewed manually — this only records the suggestion."""
    try:
        doc = await db_service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        if str(doc.get("user_id")) != str(user_id):
            raise HTTPException(status_code=403, detail="You can only suggest your own documents")
        note = (request or {}).get("note") if request else None
        await db_service.create_document_suggestion(document_id=document_id, user_id=user_id, note=note)
        return {"success": True, "message": "Thanks — we'll review this for the central library."}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to record document suggestion")
        raise HTTPException(status_code=500, detail="Failed to submit suggestion")


def _count_pages(content: bytes, file_type: str, file_name: str) -> Optional[int]:
    """Best-effort page count. PDF/PPTX have a real page/slide concept; DOCX and
    images don't (no rendering engine here), so this returns None for those —
    only the byte-size cap applies to them."""
    try:
        if file_type == "application/pdf" or file_name.lower().endswith(".pdf"):
            import PyPDF2
            from io import BytesIO
            return len(PyPDF2.PdfReader(BytesIO(content)).pages)
        if (
            file_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            or file_name.lower().endswith(".pptx")
        ):
            from pptx import Presentation
            from io import BytesIO
            return len(Presentation(BytesIO(content)).slides)
    except Exception as e:
        logger.warning(f"Page count check failed for {file_name} (continuing without it): {e}")
    return None


async def _process_upload_and_notify(
    *, content: bytes, file_name: str, file_type: str, uid: str, document_id: str
) -> None:
    """Background job: run the (slow) extract/chunk/embed/Pinecone pipeline,
    then notify the user of success or failure so they don't have to wait."""
    try:
        await doc_processor.process_document(
            file_content=content,
            file_name=file_name,
            file_type=file_type,
            user_id=uid,
            document_id=document_id,
        )
        await db_service.create_notification(
            user_id=uid,
            type="document_ready",
            title="Document ready",
            message=f"'{file_name}' has been processed — start studying or generate a quiz from it.",
            related_id=document_id,
        )
    except Exception as e:
        logger.exception(f"Background document processing failed for {document_id}")
        try:
            await db_service.update_document(document_id, {"processing_status": "failed"})
            await db_service.create_notification(
                user_id=uid,
                type="document_failed",
                title="Document processing failed",
                message=f"We couldn't process '{file_name}': {str(e)[:200]}. Please try re-uploading.",
                related_id=document_id,
            )
        except Exception:
            logger.exception(f"Failed to record failure state for document {document_id}")


@router.post("/learning/upload")
async def upload_document(
    http_request: Request,
    file: UploadFile = File(...),
    document_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
):
    """
    Upload a document and process it in the background. Returns immediately
    with status="queued" — the caller is notified (via /api/notifications)
    once processing finishes instead of blocking on it.
    If document_id is omitted, a deterministic ID is generated from a
    hash of (user_id + file_name + content), so re-uploading the same
    file is idempotent.
    """
    try:
        await enforce_rate_limit(
            http_request, "learning_upload", config.RATE_LIMIT_PER_MINUTE, 60
        )
        content = await file.read()
        file_name = file.filename or "untitled"
        file_type = file.content_type or "application/octet-stream"
        uid = resolve_user_id(
            authorization,
            user_id.strip() if user_id and str(user_id).strip() else None,
        )

        # Fast validation up front so bad uploads fail immediately rather than
        # via an async notification later.
        doc_processor.validate_file_size(content, file_type)
        max_pages = getattr(config, "MAX_DOCUMENT_PAGES", 100)
        page_count = _count_pages(content, file_type, file_name)
        if page_count is not None and page_count > max_pages:
            raise HTTPException(
                status_code=400,
                detail=f"Document has {page_count} pages, which exceeds the {max_pages}-page limit.",
            )

        if not document_id:
            content_hash = hashlib.sha256(
                f"{uid}:{file_name}".encode() + content
            ).hexdigest()[:16]
            document_id = f"doc_{content_hash}"

        existing = await db_service.get_document(document_id)
        if existing and existing.get("processed"):
            return {
                "success": True,
                "status": "ready",
                "message": "Document already processed",
                "document_id": existing["id"],
                "chunk_count": existing.get("chunk_count", 0),
                "expires_at": existing.get("pinecone_index_expires_at"),
                "already_exists": True,
            }
        if existing and existing.get("processing_status") not in ("failed", None):
            return {
                "success": True,
                "status": "queued",
                "message": "Already processing — we'll notify you when it's ready.",
                "document_id": existing["id"],
            }

        if not existing:
            await db_service.create_document(
                user_id=uid,
                name=file_name,
                file_name=file_name,
                file_type=file_type,
                file_size=len(content),
                document_id=document_id,
            )

        asyncio.create_task(
            _process_upload_and_notify(
                content=content, file_name=file_name, file_type=file_type,
                uid=uid, document_id=document_id,
            )
        )

        return {
            "success": True,
            "status": "queued",
            "message": "Uploading — we'll notify you when it's ready.",
            "document_id": document_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/learning/chat")
async def learning_chat(
    request: LearningChatRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Chat with document using RAG.
    Retrieves chat history from storage and saves new messages.
    Returns generate_quiz/play_quest flags when user asks to switch modes.
    """
    user_id = resolve_user_id(authorization, request.user_id)

    async def generate_learning_response():
        try:
            document_id = request.document_id
            if request.enrollment_id and not document_id:
                en_row = await db_service.get_user_enrollment(request.enrollment_id)
                if en_row and str(en_row.get("user_id")) == str(user_id):
                    document_id = str(en_row.get("document_id"))
            if not document_id:
                raise ValueError("Could not resolve document for this session")

            session_id = (
                request.session_id
                or request.enrollment_id
                or document_id
            )

            profession = request.profession
            subject_of_study = request.subject_of_study
            if not profession or not subject_of_study:
                user = await db_service.get_user(user_id)
                if user:
                    profession = profession or user.get("profession")
                    subject_of_study = subject_of_study or user.get("field_of_study") or profession

            filenames = []
            docs = await db_service.get_user_documents(user_id, limit=20)
            for d in docs:
                fn = d.get("file_name") or d.get("name") or "Untitled"
                filenames.append(fn)

            chat_history = await get_chat_history_from_storage(
                user_id=user_id,
                conversation_id=session_id,
                chat_type="tutor",
                document_id=document_id,
            )

            response = await _get_tutor_agent().chat(
                user_id=user_id,
                user_message=request.message,
                document_id=document_id,
                session_id=session_id,
                chat_history=chat_history,
                profession=profession,
                subject_of_study=subject_of_study,
                filenames=filenames,
                enrollment_id=request.enrollment_id,
            )

            words = response["answer"].split()
            for i, word in enumerate(words):
                is_last = i == len(words) - 1
                chunk = {
                    "content": word + " ",
                    "sources": response.get("sources", []) if is_last else None,
                    "complete": is_last
                }
                if is_last:
                    chunk["generate_quiz"] = response.get("generate_quiz", False)
                    chunk["play_quest"] = response.get("play_quest", False)
                    chunk["document_id"] = response.get("document_id")
                    chunk["enrollment_id"] = response.get("enrollment_id")
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)

        except Exception as e:
            logger.error(f"Learning chat error: {e}")
            error_chunk = {"error": str(e), "complete": True}
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_learning_response(),
        media_type="text/event-stream",
        headers=dict(SSE_STREAM_HEADERS),
    )


@router.delete("/learning/documents/{document_id}")
async def delete_document(document_id: str, user_id: Optional[str] = None):
    """
    Delete a document and its Pinecone index.
    Also deletes from S3 if S3 storage is enabled.
    """
    try:
        from service.s3_service import get_s3_service
        
        # Get document info
        doc = await db_service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete Pinecone index
        index_name = doc.get("pinecone_index_name")
        if index_name:
            try:
                await doc_processor.pinecone.delete_index(index_name)
            except Exception as e:
                logger.warning(f"Error deleting Pinecone index: {e}")
        
        # Delete from S3 if enabled
        s3_service = get_s3_service()
        if s3_service.enabled and doc.get("s3_key"):
            await s3_service.delete_file(
                user_id=doc["user_id"],
                document_id=document_id,
                file_name=doc["file_name"]
            )
        
        # Delete from database
        await db_service.update_document(document_id, {"is_active": False})
        # Or delete completely:
        # supabase.table("documents").delete().eq("id", document_id).execute()
        
        return {"success": True, "message": "Document deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail="Delete failed")


@router.post("/learning/reingest/{document_id}")
async def reingest_document(document_id: str, user_id: str):
    """
    Re-ingest an expired document from S3.
    Useful when a document has expired from vector DB but is still in S3.
    """
    try:
        result = await doc_processor.reingest_expired_document(
            document_id=document_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "message": "Document re-ingested successfully",
            "document_id": result["document_id"],
            "chunk_count": result["chunk_count"],
            "expires_at": result["expires_at"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Re-ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Re-ingestion failed")


@router.post("/learning/generate-quiz-from-document")
async def generate_quiz_from_document(
    document_id: str = Form(...),
    quiz_type: str = Form("general"),
    num_questions: int = Form(10),
    time_limit: int = Form(600),
    num_multiple_choice: Optional[int] = Form(None),
    num_open_ended: Optional[int] = Form(None),
    num_true_false: Optional[int] = Form(None),
    user_id: Optional[str] = Form(None),
    chat_context: Optional[str] = Form(None),
):
    """Generate a quiz based on document content, optionally biased toward
    whatever the learner has been discussing with the tutor (chat_context)."""
    try:
        # Get document
        doc = await db_service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        document_content = doc.get("content", "")

        quiz_context = document_content
        if chat_context and chat_context.strip():
            quiz_context = (
                "The learner has been actively discussing the following topics/questions "
                "about this document with a tutor. Prioritize quiz questions that reflect "
                f"what they were focused on:\n{chat_context.strip()[:4000]}\n\n"
                f"{document_content}"
            )

        # Use quiz agent to generate quiz
        from agents.quiz_agent import get_quiz_agent
        quiz_agent = get_quiz_agent()

        quiz_kwargs = dict(
            num_questions=num_questions,
            quiz_type=quiz_type,
            time_limit=time_limit,
            num_multiple_choice=num_multiple_choice,
            num_open_ended=num_open_ended,
            num_true_false=num_true_false,
            context=quiz_context,
        )
        try:
            quiz = await quiz_agent.generate_quiz(
                from_document=True,
                document_id=document_id,
                **quiz_kwargs,
            )
        except Exception as doc_err:
            # Vector index may have expired - fall back to the raw stored content
            # (same fallback /quiz/generate already uses)
            err_msg = str(doc_err).lower()
            if ("expired" in err_msg or "not found" in err_msg or "no document content" in err_msg) and len(document_content or "") > 200:
                quiz = await quiz_agent.generate_quiz(
                    from_document=True,
                    document_id=None,
                    text_content=document_content,
                    **quiz_kwargs,
                )
            else:
                raise

        # Save quiz with document reference
        quiz_data = quiz.model_dump(mode="json")
        await db_service.create_quiz(
            user_id=user_id or doc["user_id"],
            title=quiz.title,
            questions=quiz_data["questions"],
            quiz_type=quiz_type,
            time_limit=time_limit,
            total_questions=quiz.totalQuestions,
            source="document",
            document_id=document_id
        )
        
        return quiz_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")


@router.post("/learning/generate-game-from-document")
async def generate_game_from_document(
    document_id: str = Form(...),
    user_id: Optional[str] = Form(None),
    profession: Optional[str] = Form(None),
    era: Optional[str] = Form(None),
    natural_condition: Optional[str] = Form(None),
    total_cases: Optional[int] = Form(None),
):
    """Generate a Mediquest game scenario grounded in the uploaded document."""
    try:
        doc = await db_service.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        uid = user_id or doc.get("user_id")
        if not uid:
            raise HTTPException(status_code=400, detail="user_id is required to generate a game from this document")
        prof = profession
        if not prof:
            user = await db_service.get_user(uid)
            prof = (user or {}).get("profession", "healthcare Professional")

        from models.states import GameConfig, UserDetails, DifficultyLevel
        from agents.game_master import get_game_master_agent

        max_cases = getattr(config, "DOCUMENT_GAME_MAX_CASES", 20)
        resolved_total_cases = max(1, min(total_cases or 5, max_cases))

        game_config = GameConfig(
            profession=prof,
            era=era,
            natural_conditions=natural_condition,
            from_document=True,
            document_id=document_id,
            total_cases=resolved_total_cases,
        )
        user_details = UserDetails(user_id=uid, profession=prof)
        game_master = get_game_master_agent()

        game_world, game_state, case_state, npc_states, previous_cases = (
            await game_master.initialize_game(
                game_config=game_config,
                user_id=uid,
                user_details=user_details,
            )
        )

        state_payload = game_state.model_dump(mode="json")
        await save_mediquest_session(
            str(game_state.game_id),
            document_id=document_id,
            ordered_game_ids=[str(game_state.game_id)],
            current_index=0,
            mode={
                "from_document": True,
                "total_cases": getattr(game_state, "total_cases", None),
            },
            stages=["game_initialized"],
        )
        try:
            await db_service.create_game_state(
                user_id=uid,
                case_id=game_state.case_id,
                state=state_payload,
                document_id=document_id,
            )
        except Exception as db_err:
            logger.warning(f"Failed to persist game state: {db_err}")

        return {
            "success": True,
            "game_id": game_state.game_id,
            "game_state": state_payload,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Game generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate game")


@router.post("/learning/mark-task-completed")
async def mark_task_completed(
    study_plan_id: str = Form(...),
    task_id: str = Form(...),
):
    """Mark a study-plan daily task as completed (REST alternative to the tutor tool)."""
    ok = await db_service.mark_study_plan_task_completed(study_plan_id, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task or study plan not found")
    return {"success": True, "task_id": task_id}
