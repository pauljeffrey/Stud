-- Stud Database Schema
-- Supabase PostgreSQL with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Game States Table (Updated)
CREATE TABLE IF NOT EXISTS game_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    case_id UUID NOT NULL,
    state JSONB NOT NULL, -- Full GameState model
    is_demo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Performance Table
CREATE TABLE IF NOT EXISTS user_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    game_id UUID REFERENCES game_states(id),
    clinical_state_id TEXT NOT NULL,
    score DECIMAL(3,1) CHECK (score >= 0 AND score <= 10),
    analysis TEXT,
    strengths JSONB,
    weaknesses JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Achievements Table
CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    game_id UUID REFERENCES game_states(id),
    type TEXT NOT NULL, -- career_growth, promotion, financial_reward, etc.
    title TEXT NOT NULL,
    description TEXT,
    value DECIMAL(10,2), -- For financial rewards
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Documents Table (with expiry)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    content TEXT, -- First 10k chars for preview
    processed BOOLEAN DEFAULT FALSE,
    processing_status TEXT DEFAULT 'pending',
    pinecone_index_name TEXT,
    pinecone_index_created_at TIMESTAMPTZ,
    pinecone_index_expires_at TIMESTAMPTZ NOT NULL, -- 2 hours from upload
    chunk_count INTEGER,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Document Chunks Table (for pgvector if using Supabase)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI embedding dimension
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Learning Chat History
CREATE TABLE IF NOT EXISTS learning_chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    document_id UUID REFERENCES documents(id),
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sources JSONB, -- For RAG sources
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quizzes Table
CREATE TABLE IF NOT EXISTS quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    quiz_type TEXT,
    source TEXT, -- 'ai_knowledge' or 'document'
    document_id UUID REFERENCES documents(id),
    questions JSONB NOT NULL,
    time_limit INTEGER,
    total_questions INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quiz Results Table
CREATE TABLE IF NOT EXISTS quiz_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    quiz_id UUID REFERENCES quizzes(id),
    answers JSONB NOT NULL,
    scores JSONB, -- Per-question scores
    total_score DECIMAL(5,2),
    time_spent INTEGER,
    completed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Game Checkpoints Table
CREATE TABLE IF NOT EXISTS game_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    game_state_id UUID REFERENCES game_states(id),
    checkpoint_id TEXT NOT NULL,
    checkpoint_name TEXT,
    state JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_game_states_user_id ON game_states(user_id);
CREATE INDEX IF NOT EXISTS idx_game_states_is_demo ON game_states(is_demo);
CREATE INDEX IF NOT EXISTS idx_user_performance_user_id ON user_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_user_performance_game_id ON user_performance(game_id);
CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_expires_at ON documents(pinecone_index_expires_at);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_learning_chat_user_id ON learning_chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_chat_document_id ON learning_chat_history(document_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_user_id ON quizzes(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_results_user_id ON quiz_results(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_results_quiz_id ON quiz_results(quiz_id);

-- Vector similarity search index (for pgvector)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for game_states
CREATE TRIGGER update_game_states_updated_at BEFORE UPDATE ON game_states
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to cleanup expired documents (can be called by cron job)
CREATE OR REPLACE FUNCTION cleanup_expired_documents()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired documents (older than 2 hours)
    DELETE FROM documents
    WHERE pinecone_index_expires_at < NOW() - INTERVAL '2 hours';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
