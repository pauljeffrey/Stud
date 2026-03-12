"""
Learning API endpoints
Handles document upload, processing, and RAG-based chat
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import asyncio
from datetime import datetime
import uuid

from schema import LearningChatRequest
from service.document_processor import get_document_processor
from agents.rag_agent import get_rag_agent
from config import config
from supabase import create_client, Client

router = APIRouter()

# Initialize Supabase client
supabase: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_SERVICE_ROLE_KEY
)

# Get document processor and RAG agent
doc_processor = get_document_processor()
rag_agent = get_rag_agent()


@router.post("/learning/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_id: str = Form(...),
    user_id: str = Form(...)
):
    """Upload and process document for learning"""
    try:
        # Read file content
        content = await file.read()
        
        # Process document (extract text, chunk, embed, store in Pinecone)
        result = await doc_processor.process_document(
            file_content=content,
            file_name=file.filename,
            file_type=file.content_type or "application/octet-stream",
            user_id=user_id,
            document_id=document_id
        )
        
        return {
            "success": True,
            "message": "Document uploaded and processed",
            "document_id": result["document_id"],
            "chunk_count": result["chunk_count"],
            "expires_at": result["expires_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/learning/chat")
async def learning_chat(request: LearningChatRequest):
    """Chat with document using RAG"""
    
    async def generate_learning_response():
        try:
            # Use RAG agent to answer question
            response = await rag_agent.answer_question(
                question=request.message,
                document_id=request.document_id,
                chat_history=request.chat_history
            )
            
            # Save chat history
            supabase.table("learning_chat_history").insert({
                "user_id": "user_123",  # Get from auth in production
                "document_id": request.document_id,
                "role": "user",
                "content": request.message,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            supabase.table("learning_chat_history").insert({
                "user_id": "user_123",
                "document_id": request.document_id,
                "role": "assistant",
                "content": response["answer"],
                "sources": json.dumps(response.get("sources", [])),
                "created_at": datetime.now().isoformat()
            }).execute()
            
            # Stream the response
            words = response["answer"].split()
            for i, word in enumerate(words):
                chunk = {
                    "content": word + " ",
                    "sources": response.get("sources", []) if i == len(words) - 1 else None
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)
                
        except Exception as e:
            error_chunk = {"error": str(e)}
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_learning_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )


@router.delete("/learning/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its Pinecone index"""
    try:
        # Get document info
        doc_result = supabase.table("documents").select("pinecone_index_name").eq("id", document_id).execute()
        
        if doc_result.data:
            index_name = doc_result.data[0].get("pinecone_index_name")
            if index_name:
                # Delete Pinecone index
                try:
                    await doc_processor.pinecone.delete_index(index_name)
                except Exception as e:
                    print(f"Error deleting Pinecone index: {str(e)}")
        
        # Delete from Supabase
        result = supabase.table("documents").delete().eq("id", document_id).execute()
        
        return {"success": True, "message": "Document deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.post("/learning/generate-quiz-from-document")
async def generate_quiz_from_document(
    document_id: str = Form(...),
    quiz_type: str = Form(...),
    num_questions: int = Form(...),
    time_limit: int = Form(...)
):
    """Generate a quiz based on document content"""
    try:
        # Get document content
        doc_result = supabase.table("documents").select("content").eq("id", document_id).execute()
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_content = doc_result.data[0].get("content", "")
        
        # Use quiz agent to generate quiz (import from quiz_agent)
        from quiz_agent import generate_quiz
        quiz = await generate_quiz(
            quiz_type=quiz_type,
            num_questions=num_questions,
            time_limit=time_limit,
            context=document_content
        )
        
        # Save quiz with document reference
        quiz_data = quiz.dict()
        quiz_data["document_id"] = document_id
        result = supabase.table("quizzes").insert(quiz_data).execute()
        
        return quiz_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@router.post("/learning/generate-game-from-document")
async def generate_game_from_document(
    document_id: str = Form(...),
    profession: Optional[str] = Form(None),
    era: Optional[str] = Form(None),
    natural_condition: Optional[str] = Form(None)
):
    """Generate a game scenario based on document content"""
    try:
        # Get document content
        doc_result = supabase.table("documents").select("content").eq("id", document_id).execute()
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_content = doc_result.data[0].get("content", "")
        
        # Use GameMaster to generate scenario
        from agents.game_master import get_game_master
        game_master = get_game_master()
        
        scenario = await game_master.generate_scenario(
            prompt="Generate a medical scenario based on the document",
            from_document=True,
            document_content=document_content,
            profession=profession,
            era=era,
            natural_condition=natural_condition
        )
        
        return {
            "success": True,
            "scenario": scenario.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate game: {str(e)}")
