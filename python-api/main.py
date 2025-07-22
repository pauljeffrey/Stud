from fastapi import FastAPI, HTTPException, Depends, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import os
import json
import asyncio
import random
from datetime import datetime
import uuid
from supabase import create_client, Client
from models import *
from game_config import *
from utils import *

# Initialize FastAPI app
app = FastAPI(title="MediQuest AI Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize AI models
def get_ai_model(model_name: str = None, api_key: str = None):
    model_name = model_name or os.getenv("MODEL_NAME", "gemini-2.0-flash")
    api_key = api_key or os.getenv("MODEL_API_KEY")
    
    return GeminiModel(
        model_name, 
        provider=GoogleGLAProvider(api_key=api_key)
    )

# Game Master Agent
game_master_agent = Agent(
    get_ai_model(),
    system_prompt="""
    You are the Game Master for MediQuest, an immersive medical role-playing game.
    Your role is to:
    1. Create realistic medical scenarios based on the game state
    2. Respond to player actions with medically accurate information
    3. Adapt the scenario based on dice rolls and player decisions
    4. Maintain narrative continuity and engagement
    5. Provide educational value while keeping the experience fun
    
    Always respond in character as the Game Master, describing scenes, patient responses, 
    and medical findings in an engaging narrative style.
    """,
    output_type=str
)

# NPC Agent for patient and staff interactions
npc_agent = Agent(
    get_ai_model(),
    system_prompt="""
    You are an NPC in MediQuest. You will be given a character name and role.
    Respond authentically as that character would, considering:
    1. Their professional role and expertise level
    2. Their current emotional state and situation
    3. Realistic medical knowledge for their position
    4. Appropriate bedside manner and communication style
    
    Stay in character and provide realistic responses that advance the medical scenario.
    """,
    output_type=str
)

# Dice Effect Agent
dice_agent = Agent(
    get_ai_model(),
    system_prompt="""
    You are responsible for applying dice roll effects to medical scenarios.
    Based on the dice result (1-6), modify the scenario:
    
    1-2: Complications arise (patient condition worsens, equipment fails, etc.)
    3-4: Moderate changes (new symptoms appear, test results delayed, etc.)
    5-6: Favorable developments (patient responds well, help arrives, etc.)
    
    Describe the change dramatically and realistically, maintaining medical accuracy.
    """,
    output_type=str
)

@app.get("/")
async def root():
    return {"message": "MediQuest AI Service is running"}

@app.post("/api/game/chat")
async def game_chat(request: GameChatRequest):
    """Handle game chat with streaming AI responses"""
    
    async def generate_response():
        try:
            # Prepare context for the AI
            context = f"""
            Current Scenario: {request.game_state.current_scenario}
            Patient: {request.game_state.patient_info.name}, {request.game_state.patient_info.age}yo {request.game_state.patient_info.gender}
            Chief Complaint: {request.game_state.patient_info.chief_complaint}
            Current Condition: {request.game_state.patient_info.current_condition}
            Current Phase: {request.game_state.game_progress.current_phase}
            Player Action: {request.user_message}
            """
            
            # Get AI response
            result = await game_master_agent.run(context)
            
            # Stream the response
            words = result.output.split()
            for i, word in enumerate(words):
                chunk = {
                    "content": word + " ",
                    "scoreUpdate": 5 if i % 10 == 0 else 0  # Award points periodically
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
                
        except Exception as e:
            error_chunk = {"error": str(e)}
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )

@app.post("/api/game/dice-effect")
async def apply_dice_effect(request: DiceEffectRequest):
    """Apply dice roll effects to the game scenario"""
    
    async def generate_effect():
        try:
            context = f"""
            Dice Roll Result: {request.dice_result}
            Current Scenario: {request.game_state.current_scenario}
            Patient Condition: {request.game_state.patient_info.current_condition}
            Current Phase: {request.game_state.game_progress.current_phase}
            
            Apply the dice effect to this medical scenario.
            """
            
            result = await dice_agent.run(context)
            
            # Determine patient updates based on dice result
            patient_update = {}
            if request.dice_result <= 2:
                # Complications
                patient_update = {
                    "current_condition": "Condition has worsened - patient appears more distressed"
                }
            elif request.dice_result >= 5:
                # Improvements
                patient_update = {
                    "current_condition": "Patient appears more stable and responsive"
                }
            
            # Stream the response
            words = result.output.split()
            for i, word in enumerate(words):
                chunk = {
                    "content": word + " ",
                    "patientUpdate": patient_update if i == len(words) - 1 else None
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)
                
        except Exception as e:
            error_chunk = {"error": str(e)}
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_effect(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )

@app.post("/api/game/npc-chat")
async def npc_chat(request: NPCChatRequest):
    """Handle NPC conversations"""
    
    async def generate_npc_response():
        try:
            # Find the NPC
            npc = next((n for n in request.game_state.npcs if n.name == request.npc_name), None)
            if not npc:
                raise HTTPException(status_code=404, detail="NPC not found")
            
            context = f"""
            You are {request.npc_name}, a {npc.role} in the hospital.
            Current mood: {npc.mood}
            Patient situation: {request.game_state.patient_info.name} - {request.game_state.patient_info.chief_complaint}
            Current scenario: {request.game_state.current_scenario}
            
            The player is interacting with you. Respond as this character would.
            """
            
            result = await npc_agent.run(context)
            
            # Stream the response
            words = result.output.split()
            for word in words:
                chunk = {"content": word + " "}
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)
                
        except Exception as e:
            error_chunk = {"error": str(e)}
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_npc_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )

@app.post("/api/game/save")
async def save_game(request: SaveGameRequest):
    """Save game state to Supabase"""
    try:
        # Save to Supabase
        result = supabase.table("game_states").insert({
            "user_id": request.game_state.user_id,
            "case_id": request.game_state.case_id,
            "state": request.game_state.dict(),
            "timestamp": datetime.now().isoformat()
        }).execute()
        
        return {"success": True, "message": "Game saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save game: {str(e)}")

@app.post("/api/learning/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_id: str = Form(...)
):
    """Upload and process document for learning"""
    try:
        # Read file content
        content = await file.read()
        
        # Process document (extract text, create embeddings, etc.)
        # This is a simplified version - in production you'd use proper document processing
        text_content = content.decode('utf-8') if file.content_type == 'text/plain' else "Document processed"
        
        # Save to Supabase
        result = supabase.table("documents").insert({
            "id": document_id,
            "name": file.filename,
            "content": text_content,
            "processed": True,
            "uploaded_at": datetime.now().isoformat()
        }).execute()
        
        return {"success": True, "message": "Document uploaded and processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/learning/chat")
async def learning_chat(request: LearningChatRequest):
    """Chat with document using RAG"""
    
    async def generate_learning_response():
        try:
            # Retrieve document content
            doc_result = supabase.table("documents").select("*").eq("id", request.document_id).execute()
            if not doc_result.data:
                raise HTTPException(status_code=404, detail="Document not found")
            
            document = doc_result.data[0]
            
            # Create learning agent with document context
            learning_agent = Agent(
                get_ai_model(),
                system_prompt=f"""
                You are an AI tutor helping a medical student learn from their study materials.
                Document content: {document['content'][:2000]}...
                
                Answer questions about the document content, provide explanations, 
                and help the student understand complex medical concepts.
                Be educational, clear, and encouraging.
                """,
                output_type=str
            )
            
            # Get chat history context
            history_context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in request.chat_history[-5:]  # Last 5 messages
            ])
            
            context = f"""
            Chat History:
            {history_context}
            
            Student Question: {request.message}
            """
            
            result = await learning_agent.run(context)
            
            # Stream the response
            words = result.output.split()
            for word in words:
                chunk = {
                    "content": word + " ",
                    "sources": [f"Page reference from {document['name']}"]
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

@app.delete("/api/learning/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        result = supabase.table("documents").delete().eq("id", document_id).execute()
        return {"success": True, "message": "Document deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
