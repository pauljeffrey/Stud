from fastapi import FastAPI, HTTPException, Depends, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional, Union
from pymongo import MongoClient
from pymongo.database import Database
from datetime import datetime
import os
import uuid
import json
from models import (
    GameState, UserResponse, Scene, Scenario, Investigation, Investigations,
    ScanImage, ScanImages, PhysiologicSignal, PhysiologicSignals, AIResponse,
    GameRequest, GameResponse
)

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

# MongoDB connection
def get_db() -> Database:
    client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    return client[os.getenv("MONGODB_DB", "mediquest")]

# Routes
@app.get("/")
async def root():
    return {"message": "MediQuest AI Service is running"}

@app.post("/api/generate-response", response_model=GameResponse)
async def generate_response(request: GameRequest, db: Database = Depends(get_db)):
    """
    Generate an AI response based on the user's input and game state.
    This is the main endpoint that the Next.js frontend will call.
    """
    try:
        # Store the request in MongoDB for logging/debugging
        db.requests.insert_one(request.dict())
        
        # Process the user's response if provided
        game_state = request.game_state
        user_response = request.user_response
        
        # Generate AI response based on the game state and user response
        ai_response = generate_ai_response(game_state, user_response)
        
        # Update game state based on AI response
        updated_game_state = update_game_state(game_state, ai_response)
        
        # Store the updated game state and response
        response = GameResponse(
            game_state=updated_game_state,
            response=ai_response
        )
        
        # Log the response
        db.responses.insert_one(response.dict())
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.post("/api/save-checkpoint")
async def save_checkpoint(game_state: GameState, db: Database = Depends(get_db)):
    """
    Save the current game state as a checkpoint.
    """
    try:
        # Generate checkpoint ID if not provided
        checkpoint_id = f"checkpoint_{uuid.uuid4()}"
        
        # Save game state to MongoDB
        db.checkpoints.insert_one({
            "checkpoint_id": checkpoint_id,
            "user_id": game_state.user_id,
            "case_id": game_state.case_id,
            "game_state": game_state.dict(),
            "timestamp": datetime.now()
        })
        
        return {
            "success": True,
            "message": "Checkpoint saved successfully",
            "checkpoint_id": checkpoint_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving checkpoint: {str(e)}")

@app.get("/api/load-checkpoint/{user_id}/{checkpoint_id}")
async def load_checkpoint(
    user_id: str, 
    checkpoint_id: str, 
    db: Database = Depends(get_db)
):
    """
    Load a game state from a checkpoint.
    """
    try:
        checkpoint = db.checkpoints.find_one({
            "user_id": user_id,
            "checkpoint_id": checkpoint_id
        })
        
        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        
        return GameState(**checkpoint["game_state"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading checkpoint: {str(e)}")

@app.get("/api/list-checkpoints/{user_id}")
async def list_checkpoints(user_id: str, db: Database = Depends(get_db)):
    """
    List all checkpoints for a user.
    """
    try:
        checkpoints = list(db.checkpoints.find(
            {"user_id": user_id},
            {"_id": 0, "checkpoint_id": 1, "case_id": 1, "timestamp": 1}
        ).sort("timestamp", -1))
        
        return {"checkpoints": checkpoints}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing checkpoints: {str(e)}")

@app.post("/api/upload-context")
async def upload_context(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    user_id: str = Form(...),
    context_type: str = Form(...),
    db: Database = Depends(get_db)
):
    """
    Upload a file or URL to be used as context for generating questions or scenarios.
    """
    try:
        context_id = f"context_{uuid.uuid4()}"
        context_data = {
            "context_id": context_id,
            "user_id": user_id,
            "context_type": context_type,
            "timestamp": datetime.now()
        }
        
        if file:
            # Read and store file content
            content = await file.read()
            # Store in MongoDB (for small files) or file system (for larger files)
            # This is a simplified example - in production you might want to use GridFS for larger files
            context_data["file_name"] = file.filename
            context_data["content"] = content.decode("utf-8")
            context_data["source_type"] = "file"
        elif url:
            # Store URL for later processing
            context_data["url"] = url
            context_data["source_type"] = "url"
        else:
            raise HTTPException(status_code=400, detail="Either file or URL must be provided")
        
        db.contexts.insert_one(context_data)
        
        return {
            "success": True,
            "message": "Context uploaded successfully",
            "context_id": context_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading context: {str(e)}")

@app.post("/api/generate-quiz")
async def generate_quiz(
    user_id: str,
    quiz_type: str,  # "open", "true_false", "multichoice"
    num_questions: Optional[int] = 10,
    time_limit: Optional[int] = 600,  # in seconds
    context_id: Optional[str] = None,
    db: Database = Depends(get_db)
):
    """
    Generate a quiz based on the specified parameters and optional context.
    """
    try:
        # If context_id is provided, retrieve the context
        context = None
        if context_id:
            context_doc = db.contexts.find_one({"context_id": context_id})
            if context_doc:
                if context_doc["source_type"] == "file":
                    context = context_doc["content"]
                else:  # URL
                    # In a real implementation, you would fetch and process the URL content
                    context = f"Content from URL: {context_doc['url']}"
        
        # Generate quiz questions
        questions = generate_quiz_questions(quiz_type, num_questions, context)
        
        # Create a new game state for the quiz
        quiz_id = f"quiz_{uuid.uuid4()}"
        
        quiz_data = {
            "quiz_id": quiz_id,
            "user_id": user_id,
            "quiz_type": quiz_type,
            "num_questions": num_questions,
            "time_limit": time_limit,
            "questions": questions,
            "timestamp": datetime.now()
        }
        
        db.quizzes.insert_one(quiz_data)
        
        return {
            "success": True,
            "quiz_id": quiz_id,
            "questions": questions,
            "time_limit": time_limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")

# Helper functions
def generate_ai_response(game_state: GameState, user_response: Optional[UserResponse]) -> AIResponse:
    """
    Generate an AI response based on the game state and user response.
    In a real implementation, this would call your AI model.
    """
    # This is a placeholder implementation
    # In a real app, you would use an AI model to generate the response
    
    case_id = game_state.case_id
    
    # Example scenario
    scenario = Scenario(
        scenes=[
            Scene(description="Patient presents with chest pain and shortness of breath.")
        ]
    )
    
    # Default response
    response = AIResponse(
        scenario=scenario,
        question="What would you like to do next?",
        options=["Examine patient", "Order ECG", "Order blood tests", "Administer medication"],
        answer="",
        clue="Consider the patient's symptoms and what tests might be appropriate.",
        time="300"  # 5 minutes
    )
    
    # If user provided a response, process it
    if user_response:
        if "ecg" in user_response.answer.lower():
            # Blood investigation example
            investigations = Investigations(
                result=[
                    Investigation(
                        type="ECG",
                        result={"finding": "ST-segment elevation in leads II, III, and aVF"}
                    )
                ]
            )
            
            # Update response with investigation results
            response.blood_investigation = investigations
            response.question = "The ECG shows ST-segment elevation. What's your diagnosis?"
            response.options = ["Myocardial infarction", "Angina", "Pericarditis", "Pulmonary embolism"]
            response.answer = "Myocardial infarction"
            response.clue = "ST-segment elevation is a classic sign of myocardial infarction."
            
        elif "blood" in user_response.answer.lower():
            # Blood investigation example
            investigations = Investigations(
                result=[
                    Investigation(
                        type="Troponin",
                        result={"value": "2.3 ng/mL", "reference": "<0.04 ng/mL"}
                    ),
                    Investigation(
                        type="CK-MB",
                        result={"value": "25 U/L", "reference": "<5 U/L"}
                    )
                ]
            )
            
            # Update response with investigation results
            response.blood_investigation = investigations
            response.question = "Blood tests show elevated cardiac markers. What's your next step?"
            response.options = ["Administer aspirin", "Order coronary angiography", "Start thrombolytic therapy", "Consult cardiology"]
            
        elif "ct" in user_response.answer.lower() or "scan" in user_response.answer.lower():
            # Scan image example
            scan_images = ScanImages(
                result=[
                    ScanImage(
                        type="CT Scan",
                        result={"url": "/placeholder.svg?height=300&width=500"},
                        report="CT scan shows evidence of subarachnoid hemorrhage."
                    )
                ]
            )
            
            # Update response with scan results
            response.scan = scan_images
            response.question = "The CT scan shows subarachnoid hemorrhage. What's your next step?"
            response.options = ["Consult neurosurgery", "Administer mannitol", "Order cerebral angiography", "Transfer to ICU"]
    
    return response

def update_game_state(game_state: GameState, ai_response: AIResponse) -> GameState:
    """
    Update the game state based on the AI response.
    """
    # Update the game state with the new information
    # This is a simplified implementation
    game_state.current_scenario = ai_response.scenario
    game_state.current_question = ai_response.question
    game_state.options = ai_response.options
    game_state.time_remaining = int(ai_response.time)
    
    # Add the AI response to the message history
    game_state.messages.append({
        "role": "system",
        "content": ai_response.question,
        "timestamp": datetime.now().isoformat()
    })
    
    return game_state

def generate_quiz_questions(quiz_type: str, num_questions: int, context: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate quiz questions based on the specified type and context.
    In a real implementation, this would use an AI model.
    """
    # This is a placeholder implementation
    # In a real app, you would use an AI model to generate questions based on the context
    
    questions = []
    
    # Example questions for different quiz types
    if quiz_type == "open":
        questions = [
            {
                "id": f"q{i}",
                "question": f"Open question {i}",
                "answer": f"Answer for question {i}"
            }
            for i in range(1, num_questions + 1)
        ]
    elif quiz_type == "true_false":
        questions = [
            {
                "id": f"q{i}",
                "question": f"True/False question {i}",
                "options": ["True", "False"],
                "answer": "True" if i % 2 == 0 else "False"
            }
            for i in range(1, num_questions + 1)
        ]
    elif quiz_type == "multichoice":
        questions = [
            {
                "id": f"q{i}",
                "question": f"Multiple choice question {i}",
                "options": [f"Option A for question {i}", f"Option B for question {i}", 
                           f"Option C for question {i}", f"Option D for question {i}"],
                "answer": f"Option A for question {i}"  # First option is correct for simplicity
            }
            for i in range(1, num_questions + 1)
        ]
    
    return questions

# Run the app with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)