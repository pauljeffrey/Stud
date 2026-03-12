-- Complete Stud Database Schema
-- This file contains all SQL statements to create the necessary tables for the application
-- Includes all tables referenced in user.py and game_v2.py

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- AUTHENTICATION & USER MANAGEMENT
-- ============================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    profession TEXT,
    age INTEGER,
    avatar_url TEXT,
    bio TEXT,
    api_settings JSONB DEFAULT '{}',
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token TEXT,
    password_reset_token TEXT,
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- GAME MANAGEMENT
-- ============================================

-- Game states table
CREATE TABLE IF NOT EXISTS game_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    case_id TEXT NOT NULL,
    state JSONB NOT NULL,
    scenario_type TEXT DEFAULT 'standard', -- 'standard' or 'document_based'
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    is_demo BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Game checkpoints table
CREATE TABLE IF NOT EXISTS game_checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_state_id UUID REFERENCES game_states(id) ON DELETE CASCADE,
    checkpoint_id TEXT NOT NULL,
    checkpoint_name TEXT,
    state JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, game_state_id, checkpoint_id)
);

-- Game statistics table
CREATE TABLE IF NOT EXISTS game_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    games_created INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    games_completed INTEGER DEFAULT 0,
    total_score BIGINT DEFAULT 0,
    total_time_played INTEGER DEFAULT 0, -- in seconds
    average_score DECIMAL(5,2),
    highest_score INTEGER DEFAULT 0,
    last_played_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Game creation log
CREATE TABLE IF NOT EXISTS game_creation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    game_state_id UUID REFERENCES game_states(id) ON DELETE SET NULL,
    scenario_type TEXT,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User performance table
CREATE TABLE IF NOT EXISTS user_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID REFERENCES game_states(id) ON DELETE CASCADE,
    clinical_state_id TEXT NOT NULL,
    score DECIMAL(3,1) CHECK (score >= 0 AND score <= 10),
    analysis TEXT,
    strengths JSONB,
    weaknesses JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- QUIZ MANAGEMENT
-- ============================================

-- Quizzes table
CREATE TABLE IF NOT EXISTS quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    questions JSONB NOT NULL,
    quiz_type TEXT NOT NULL, -- 'multiple_choice', 'true_false', 'open_ended'
    time_limit INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    difficulty TEXT DEFAULT 'intermediate', -- 'beginner', 'intermediate', 'advanced'
    source TEXT DEFAULT 'ai_knowledge', -- 'ai_knowledge' or 'document'
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quiz results table
CREATE TABLE IF NOT EXISTS quiz_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    answers JSONB NOT NULL,
    scores JSONB, -- Per-question scores
    score INTEGER NOT NULL,
    total_score DECIMAL(5,2),
    time_spent INTEGER NOT NULL, -- in seconds
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Saved quizzes (user's favorite quizzes)
CREATE TABLE IF NOT EXISTS saved_quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, quiz_id)
);

-- Quiz statistics table
CREATE TABLE IF NOT EXISTS quiz_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quizzes_taken INTEGER DEFAULT 0,
    quizzes_passed INTEGER DEFAULT 0,
    total_score BIGINT DEFAULT 0,
    average_score DECIMAL(5,2),
    highest_score INTEGER DEFAULT 0,
    total_time_spent INTEGER DEFAULT 0, -- in seconds
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================
-- LEARNING & DOCUMENTS
-- ============================================

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content TEXT, -- First 10k chars for preview
    processed BOOLEAN DEFAULT FALSE,
    processing_status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    pinecone_index_name TEXT, -- Temporary Pinecone index name
    pinecone_index_created_at TIMESTAMP WITH TIME ZONE,
    pinecone_index_expires_at TIMESTAMP WITH TIME ZONE NOT NULL, -- Default 2 hours from creation
    chunk_count INTEGER DEFAULT 0,
    embedding_model TEXT DEFAULT 'text-embedding-3-small',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document chunks table (for RAG with pgvector)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536), -- Using pgvector extension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

-- Learning chat history
CREATE TABLE IF NOT EXISTS learning_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- ACHIEVEMENTS & PROGRESSION
-- ============================================

-- Achievements table (simplified - stores user achievements directly)
CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID REFERENCES game_states(id) ON DELETE SET NULL,
    type TEXT NOT NULL, -- 'career_growth', 'promotion', 'financial_reward', 'certification', etc.
    title TEXT NOT NULL,
    description TEXT,
    value DECIMAL(10,2), -- For financial rewards
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Achievement definitions table
CREATE TABLE IF NOT EXISTS achievement_definitions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    icon TEXT NOT NULL,
    category TEXT NOT NULL, -- 'game', 'quiz', 'learning', 'social'
    points INTEGER DEFAULT 0,
    rarity TEXT DEFAULT 'common', -- 'common', 'rare', 'epic', 'legendary'
    criteria JSONB NOT NULL, -- Criteria for unlocking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User achievements table (for tracking progress)
CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_id TEXT REFERENCES achievement_definitions(id) ON DELETE CASCADE,
    progress JSONB DEFAULT '{}', -- Current progress towards achievement
    unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- User progression table
CREATE TABLE IF NOT EXISTS user_progression (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    level INTEGER DEFAULT 1,
    experience_points BIGINT DEFAULT 0,
    total_quests_completed INTEGER DEFAULT 0,
    total_quizzes_completed INTEGER DEFAULT 0,
    total_learning_hours DECIMAL(10,2) DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Session indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

-- Game indexes
CREATE INDEX IF NOT EXISTS idx_game_states_user_id ON game_states(user_id);
CREATE INDEX IF NOT EXISTS idx_game_states_case_id ON game_states(case_id);
CREATE INDEX IF NOT EXISTS idx_game_states_active ON game_states(is_active);
CREATE INDEX IF NOT EXISTS idx_game_states_is_demo ON game_states(is_demo);
CREATE INDEX IF NOT EXISTS idx_game_checkpoints_user_id ON game_checkpoints(user_id);
CREATE INDEX IF NOT EXISTS idx_game_checkpoints_game_state_id ON game_checkpoints(game_state_id);
CREATE INDEX IF NOT EXISTS idx_user_performance_user_id ON user_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_user_performance_game_id ON user_performance(game_id);

-- Quiz indexes
CREATE INDEX IF NOT EXISTS idx_quizzes_user_id ON quizzes(user_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_created_at ON quizzes(created_at);
CREATE INDEX IF NOT EXISTS idx_quiz_results_user_id ON quiz_results(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_results_quiz_id ON quiz_results(quiz_id);
CREATE INDEX IF NOT EXISTS idx_saved_quizzes_user_id ON saved_quizzes(user_id);

-- Document indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed);
CREATE INDEX IF NOT EXISTS idx_documents_pinecone_expires ON documents(pinecone_index_expires_at);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_learning_chat_user_doc ON learning_chat_history(user_id, document_id);

-- Achievement indexes
CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_unlocked ON user_achievements(unlocked);

-- Statistics indexes
CREATE INDEX IF NOT EXISTS idx_game_statistics_user_id ON game_statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_statistics_user_id ON quiz_statistics(user_id);

-- Vector similarity search index (for pgvector)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_game_states_updated_at BEFORE UPDATE ON game_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quizzes_updated_at BEFORE UPDATE ON quizzes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to cleanup expired documents
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

-- Function to update game statistics
CREATE OR REPLACE FUNCTION update_game_statistics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO game_statistics (user_id, games_created, games_played)
    VALUES (NEW.user_id, 1, 1)
    ON CONFLICT (user_id) DO UPDATE
    SET games_created = game_statistics.games_created + 1,
        games_played = game_statistics.games_played + 1,
        updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for game statistics
CREATE TRIGGER update_game_stats_on_insert
    AFTER INSERT ON game_states
    FOR EACH ROW EXECUTE FUNCTION update_game_statistics();

-- Function to update quiz statistics
CREATE OR REPLACE FUNCTION update_quiz_statistics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO quiz_statistics (user_id, quizzes_taken, total_score, average_score)
    VALUES (
        NEW.user_id,
        1,
        NEW.score,
        NEW.score
    )
    ON CONFLICT (user_id) DO UPDATE
    SET quizzes_taken = quiz_statistics.quizzes_taken + 1,
        total_score = quiz_statistics.total_score + NEW.score,
        average_score = (quiz_statistics.total_score + NEW.score)::DECIMAL / (quiz_statistics.quizzes_taken + 1),
        updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for quiz statistics
CREATE TRIGGER update_quiz_stats_on_insert
    AFTER INSERT ON quiz_results
    FOR EACH ROW EXECUTE FUNCTION update_quiz_statistics();
