"""
Authentication API endpoints
Handles user registration, login, session management, and password reset
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
import secrets
import uuid

from config import config
from supabase import create_client, Client

router = APIRouter()
security = HTTPBearer()

# Initialize Supabase client
supabase: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_SERVICE_ROLE_KEY
)

# JWT settings
JWT_SECRET = config.SECRET_KEY or "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    profession: Optional[str] = None
    age: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_jwt_token(user_id: str, email: str) -> str:
    """Create a JWT token for a user"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    # Get user from database
    user_result = supabase.table("users").select("*").eq("id", payload["user_id"]).execute()
    if not user_result.data:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user_result.data[0]


@router.post("/auth/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = supabase.table("users").select("id").eq("email", request.email).execute()
        if existing_user.data:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        password_hash = hash_password(request.password)
        
        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        
        # Create user
        user_data = {
            "id": str(uuid.uuid4()),
            "email": request.email,
            "password_hash": password_hash,
            "name": request.name,
            "profession": request.profession,
            "age": request.age,
            "email_verification_token": verification_token,
            "email_verified": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("users").insert(user_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        user_id = result.data[0]["id"]
        
        # Create initial user progression record
        supabase.table("user_progression").insert({
            "user_id": user_id,
            "level": 1,
            "experience_points": 0
        }).execute()
        
        # Create initial statistics records
        supabase.table("game_statistics").insert({
            "user_id": user_id,
            "games_created": 0,
            "games_played": 0
        }).execute()
        
        supabase.table("quiz_statistics").insert({
            "user_id": user_id,
            "quizzes_taken": 0,
            "quizzes_passed": 0
        }).execute()
        
        # Create JWT token
        token = create_jwt_token(user_id, request.email)
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        supabase.table("user_sessions").insert({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": (datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS)).isoformat(),
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user": {
                "id": user_id,
                "email": request.email,
                "name": request.name
            },
            "token": token,
            "session_token": session_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/auth/login")
async def login(request: LoginRequest):
    """Login user"""
    try:
        # Get user from database
        user_result = supabase.table("users").select("*").eq("email", request.email).execute()
        
        if not user_result.data:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = user_result.data[0]
        
        # Verify password
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        user_id = user["id"]
        
        # Update last login
        supabase.table("users").update({
            "last_login": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        # Create JWT token
        token = create_jwt_token(user_id, request.email)
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        supabase.table("user_sessions").insert({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": (datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS)).isoformat(),
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user_id,
                "email": user["email"],
                "name": user["name"],
                "profession": user.get("profession")
            },
            "token": token,
            "session_token": session_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (invalidate session)"""
    try:
        user_id = current_user["id"]
        
        # Delete all user sessions
        supabase.table("user_sessions").delete().eq("user_id", user_id).execute()
        
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")


@router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "success": True,
        "user": {
            "id": current_user["id"],
            "email": current_user["email"],
            "name": current_user["name"],
            "profession": current_user.get("profession"),
            "age": current_user.get("age"),
            "avatar_url": current_user.get("avatar_url"),
            "bio": current_user.get("bio")
        }
    }


@router.post("/auth/password-reset")
async def request_password_reset(request: PasswordResetRequest):
    """Request password reset"""
    try:
        # Get user
        user_result = supabase.table("users").select("id").eq("email", request.email).execute()
        if not user_result.data:
            # Don't reveal if email exists for security
            return {"success": True, "message": "If email exists, reset link has been sent"}
        
        user_id = user_result.data[0]["id"]
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)  # 1 hour expiration
        
        # Save reset token
        supabase.table("users").update({
            "password_reset_token": reset_token,
            "password_reset_expires": expires_at.isoformat()
        }).eq("id", user_id).execute()
        
        # In production, send email with reset link
        # For now, just return success
        
        return {"success": True, "message": "If email exists, reset link has been sent", "token": reset_token}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset request failed: {str(e)}")


@router.post("/auth/password-reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirm):
    """Confirm password reset with token"""
    try:
        # Find user with reset token
        user_result = supabase.table("users").select("*").eq("password_reset_token", request.token).execute()
        
        if not user_result.data:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        user = user_result.data[0]
        
        # Check expiration
        if user.get("password_reset_expires"):
            expires_at = datetime.fromisoformat(user["password_reset_expires"].replace('Z', '+00:00'))
            if datetime.now() > expires_at:
                raise HTTPException(status_code=400, detail="Reset token has expired")
        
        # Hash new password
        password_hash = hash_password(request.new_password)
        
        # Update password and clear reset token
        supabase.table("users").update({
            "password_hash": password_hash,
            "password_reset_token": None,
            "password_reset_expires": None,
            "updated_at": datetime.now().isoformat()
        }).eq("id", user["id"]).execute()
        
        return {"success": True, "message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

