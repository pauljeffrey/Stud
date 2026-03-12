import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.quiz import router as quiz_router
try:
    from api.quiz_v2 import router as quiz_v2_router
except ImportError:
    quiz_v2_router = None
from api.learning import router as learning_router
from api.game import router as game_router
from api.game_v2 import router as game_v2_router
from api.auth import router as auth_router
from api.cleanup import router as cleanup_router
from api.user import router as user_router
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Colors for terminal output (if supported)
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(message: str):
    """Print success message"""
    logger.info(f"{Colors.GREEN}✓{Colors.RESET} {message}")

def print_error(message: str):
    """Print error message"""
    logger.error(f"{Colors.RED}✗{Colors.RESET} {message}")

def print_info(message: str):
    """Print info message"""
    logger.info(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")

def print_warning(message: str):
    """Print warning message"""
    logger.warning(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")

async def initialize_components():
    """Initialize all backend components"""
    print_info("=" * 70)
    print_info(f"{Colors.BOLD}{Colors.CYAN}Initializing Stud AI Backend Service{Colors.RESET}")
    print_info("=" * 70)
    
    # 1. Check configuration
    print_info("Checking configuration...")
    if not config.SUPABASE_URL:
        print_error("SUPABASE_URL is not set")
        raise ValueError("SUPABASE_URL is required")
    print_success(f"Supabase URL configured: {config.SUPABASE_URL[:40]}...")
    
    if not config.SUPABASE_SERVICE_ROLE_KEY:
        print_error("SERVICE_ROLE_KEY is not set")
        raise ValueError("SERVICE_ROLE_KEY is required")
    print_success("Supabase Service Role Key configured")
    
    if not config.SECRET_KEY:
        print_error("SECRET_KEY is not set")
        raise ValueError("SECRET_KEY is required for JWT authentication")
    print_success("JWT Secret Key configured")
    
    # 2. Test Supabase connection
    print_info("Testing Supabase connection...")
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_ROLE_KEY
        )
        # Test connection by querying a simple table
        result = supabase.table("users").select("id").limit(1).execute()
        print_success("Supabase connection successful")
        print_info(f"  Database: Connected to {config.SUPABASE_URL.split('//')[1].split('.')[0]}")
    except Exception as e:
        print_error(f"Supabase connection failed: {str(e)}")
        raise
    
    # 3. Test Redis connection (optional)
    print_info("Testing Redis connection...")
    if config.REDIS_URL:
        try:
            import redis.asyncio as redis
            redis_client = await redis.from_url(config.REDIS_URL)
            await redis_client.ping()
            print_success(f"Redis connection successful")
            print_info(f"  Host: {config.REDIS_HOST}:{config.REDIS_PORT}")
            await redis_client.close()
        except Exception as e:
            print_warning(f"Redis connection failed (optional): {str(e)}")
            print_warning("Continuing without Redis cache...")
    else:
        print_warning("Redis URL not configured (optional - caching disabled)")
    
    # 4. Check AI API keys
    print_info("Checking AI API keys...")
    ai_keys_configured = False
    if config.GOOGLE_API_KEY:
        print_success("Google Gemini API key configured")
        ai_keys_configured = True
    else:
        print_warning("Google Gemini API key not set")
    
    if config.OPENAI_API_KEY:
        print_success("OpenAI API key configured")
        ai_keys_configured = True
    else:
        print_warning("OpenAI API key not set")
    
    if not ai_keys_configured:
        print_warning("No AI API keys configured - some features may not work")
    
    # 5. Check Pinecone (optional)
    print_info("Checking Pinecone configuration...")
    try:
        pinecone_key = os.getenv("PINECONE_API_KEY")
        if pinecone_key:
            print_success("Pinecone API key configured")
            print_info("  Document vector storage: Enabled")
        else:
            print_warning("Pinecone API key not set (document chat may not work)")
    except Exception as e:
        print_warning(f"Pinecone check failed: {str(e)}")
    
    # 6. Verify file directories
    print_info("Checking file directories...")
    directories = [
        getattr(config, 'UPLOAD_FOLDER', '/tmp/uploads'),
        getattr(config, 'IMAGE_TEMP_DIR', '/tmp/images'),
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print_success(f"Directory ready: {directory}")
    
    # 7. Verify routers
    print_info("Loading API routers...")
    routers_loaded = []
    routers_loaded.append("Authentication")
    routers_loaded.append("User")
    routers_loaded.append("Quiz (Legacy)")
    if quiz_v2_router:
        routers_loaded.append("Quiz V2")
    routers_loaded.append("Learning")
    routers_loaded.append("Game (Legacy)")
    routers_loaded.append("Game V2")
    routers_loaded.append("Cleanup")
    
    for router_name in routers_loaded:
        print_success(f"Router loaded: {router_name}")
    
    print_info("=" * 70)
    print_success(f"{Colors.BOLD}All components initialized successfully!{Colors.RESET}")
    print_info("=" * 70)
    print_info(f"{Colors.CYAN}Server starting on http://0.0.0.0:8000{Colors.RESET}")
    print_info(f"{Colors.CYAN}API Documentation: http://0.0.0.0:8000/docs{Colors.RESET}")
    print_info("=" * 70)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    await initialize_components()
    yield
    # Shutdown (if needed)
    logger.info("Shutting down Stud AI Backend Service...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Stud AI Service",
    description="Backend API for Stud medical education platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(user_router, prefix="/api", tags=["User"])
app.include_router(quiz_router, prefix="/api", tags=["Quiz (Legacy)"])
if quiz_v2_router:
    app.include_router(quiz_v2_router, prefix="/api", tags=["Quiz V2"])
app.include_router(learning_router, prefix="/api", tags=["Learning"])
app.include_router(game_router, prefix="/api", tags=["Game (Legacy)"])
app.include_router(game_v2_router, prefix="/api", tags=["Game V2"])
app.include_router(cleanup_router, prefix="/api", tags=["Cleanup"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Stud AI Service is running",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Quick database check
        from supabase import create_client
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        supabase.table("users").select("id").limit(1).execute()
        
        return {
            "status": "healthy",
            "service": "Stud AI Service",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "Stud AI Service",
            "database": "disconnected",
            "error": str(e)
        }, 503


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
