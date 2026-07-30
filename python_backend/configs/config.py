import os
from dotenv import load_dotenv

load_dotenv()

    
class Config:
    # Database Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SERVICE_ROLE_KEY")
    
    
    GAME_MASTER_MODEL_NAME = os.getenv("GAME_MASTER_MODEL_NAME")
    NPC_MODEL_NAME = os.getenv("NPC_MODEL_NAME")
    TUTOR_MODEL_NAME=os.getenv("RAG_MODEL_NAME")
    STATE_CONTROLLER_MODEL_NAME = os.getenv("STATE_CONTROLLER_MODEL_NAME")
    QUIZ_MODEL_NAME=os.getenv("QUIZ_MODEL_NAME")
    GAME_WORLD_MODEL_NAME=os.getenv("GAME_WORLD_MODEL_NAME") or os.getenv("GAME_WORLD_MODEL_MODEL_NAME")
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME")
    
    # Build Redis URL if not provided
    if not REDIS_URL:
        if REDIS_PASSWORD:
            REDIS_URL = f"redis://{REDIS_USERNAME or ''}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
        else:
            REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
    
    # AI Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None) 
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    
    # Application Settings
    SECRET_KEY = os.getenv("SECRET_KEY")
    CHAT_MEMORY_EXPIRE_SECONDS = int(os.getenv("CHAT_MEMORY_EXPIRE_SECONDS", "86400"))
    CHAT_HISTORY_WINDOW = int(os.getenv("CHAT_HISTORY_WINDOW", "200"))
    
    # File Storage Configuration (Production defaults)
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp/uploads")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # Production: 10MB, Free tier: 5MB (5242880)
    IMAGE_TEMP_DIR = os.getenv("IMAGE_TEMP_DIR", "/tmp/images")
    MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "5242880"))  # Production: 5MB, Free tier: 2.5MB (2621440)
    MAX_DOCUMENT_PAGES = int(os.getenv("MAX_DOCUMENT_PAGES", "100"))  # PDF pages / PPTX slides; no true page count for DOCX/images
    USE_S3_STORAGE = os.getenv("USE_S3_STORAGE", "false").lower() == "true"  # Production: True, Free tier: False
    
    # Analytics Configuration
    ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    ANALYTICS_FLUSH_INTERVAL = int(os.getenv("ANALYTICS_FLUSH_INTERVAL", "3600"))
    
    # Security Configuration
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    GAME_MASTER_NAME = str(os.getenv("GAME_MASTER_NAME", 'Dr. Aegis'))
    N_CHAT_SESSIONS = int(os.getenv("N_CHAT_SESSIONS", '3'))
    CONFIDENCE_SCORE_THRESHOLD = float(os.getenv('CONFIDENCE_SCORE_THRESHOLD', 0.5))
    
    MAX_TOKENS= int(os.getenv("MAX_TOKENS", "128000"))
    AGENT_RESULT_RETRIES = int(os.getenv("AGENT_RESULT_RETRIES", "2"))
    INIT_OUTPUT_RETRIES = int(os.getenv("INIT_OUTPUT_RETRIES", "2"))
    SERPER_API_KEY = str(os.getenv('SERPER_API_KEY'))
    DATABASE_ENGINE = os.getenv("DATABASE_ENGINE", "supabase")  # Default to "supabase" for testing, or "mssql" for production
    AI_CHAT_ID = os.getenv("AI_CHAT_ID",)
    
    # Chat History Configuration
    MAX_ACTIVE_CHAT_MESSAGES = int(os.getenv("MAX_ACTIVE_CHAT_MESSAGES", "100"))
    # NOTE: only DB_THREAD_POOL_SIZE (read directly via os.getenv in main.py)
    # actually controls concurrency — supabase-py's HTTP client and the redis
    # client don't use a traditional connection-pool concept, so the
    # DB_POOL_*/REDIS_POOL_* settings this file used to have were dead config
    # and have been removed.

    # Agent Timeout Configuration (Production defaults)
    AGENT_TIMEOUT = float(os.getenv("AGENT_TIMEOUT", "300.0"))
    AGENT_SPECIFIC_TIMEOUT = float(os.getenv("AGENT_SPECIFIC_TIMEOUT", "280.0"))
    MODEL_TIMEOUT = float(os.getenv("MODEL_TIMEOUT", "180.0"))

    # Document Mediquest: smaller persisted chunks; agents pull adjacent rows as needed
    DOCUMENT_CHUNK_WORDS = int(os.getenv("DOCUMENT_CHUNK_WORDS", "1000"))
    DOCUMENT_CHUNK_OVERLAP = int(os.getenv("DOCUMENT_CHUNK_OVERLAP", "200"))
    MAX_EXTRACTED_WORDS = int(os.getenv("MAX_EXTRACTED_WORDS", "200000"))  # cap before chunking (memory)
    PINECONE_INDEX_EXPIRATION_HOURS = int(os.getenv("PINECONE_INDEX_EXPIRATION_HOURS", "2"))
    DOCUMENT_GAME_MAX_CASES = int(os.getenv("DOCUMENT_GAME_MAX_CASES", "20"))
    DOCUMENT_GAME_RELEVANCE_THRESHOLD = float(os.getenv("DOCUMENT_GAME_RELEVANCE_THRESHOLD", "0.35"))
    DOCUMENT_GAME_MAX_REFINE_TOOL_ROUNDS = int(os.getenv("DOCUMENT_GAME_MAX_REFINE_TOOL_ROUNDS", "8"))
    DOCUMENT_GAME_JOB_REDIS_TTL = int(os.getenv("DOCUMENT_GAME_JOB_TTL", str(7 * 24 * 3600)))
    DOCUMENT_GAME_LLM_BUDGET_UNITS = int(os.getenv("DOCUMENT_GAME_LLM_BUDGET_UNITS", "500000"))  # soft cap per job
    # Optional: prefix Redis keys for job queue (worker drains in production)
    DOCUMENT_GAME_QUEUE_KEY = os.getenv("DOCUMENT_GAME_QUEUE_KEY", "q:dg")
   

config = Config()
