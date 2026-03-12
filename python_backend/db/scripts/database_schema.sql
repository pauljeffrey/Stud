-- MediQuest Database Schema
-- This file contains all SQL statements to create the necessary tables for the application

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
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

-- ============================================
-- QUIZ MANAGEMENT
-- ============================================

-- Quizzes table
CREATE TABLE IF NOT EXISTS quizzes (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    questions JSONB NOT NULL,
    quiz_type TEXT NOT NULL, -- 'multiple_choice', 'true_false', 'open_ended'
    time_limit INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    difficulty TEXT DEFAULT 'intermediate', -- 'beginner', 'intermediate', 'advanced'
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quiz results table
CREATE TABLE IF NOT EXISTS quiz_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id TEXT REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    answers JSONB NOT NULL,
    score INTEGER NOT NULL,
    time_spent INTEGER NOT NULL, -- in seconds
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Saved quizzes (user's favorite quizzes)
CREATE TABLE IF NOT EXISTS saved_quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quiz_id TEXT REFERENCES quizzes(id) ON DELETE CASCADE,
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
    content TEXT,
    processed BOOLEAN DEFAULT FALSE,
    processing_status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    pinecone_index_name TEXT, -- Temporary Pinecone index name
    pinecone_index_created_at TIMESTAMP WITH TIME ZONE,
    pinecone_index_expires_at TIMESTAMP WITH TIME ZONE, -- Default 4 hours from creation
    chunk_count INTEGER DEFAULT 0,
    embedding_model TEXT DEFAULT 'text-embedding-3-small',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document chunks table (for RAG)
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

-- Achievements definition table
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

-- User achievements table
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
-- ANALYTICS & METRICS
-- ============================================

-- API requests tracking
CREATE TABLE IF NOT EXISTS api_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Game creation tracking
CREATE TABLE IF NOT EXISTS game_creation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    game_state_id UUID REFERENCES game_states(id) ON DELETE SET NULL,
    scenario_type TEXT,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quiz generation tracking
CREATE TABLE IF NOT EXISTS quiz_generation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    quiz_id TEXT REFERENCES quizzes(id) ON DELETE SET NULL,
    quiz_type TEXT,
    num_questions INTEGER,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    generation_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily analytics aggregation
CREATE TABLE IF NOT EXISTS daily_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    games_created INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    quizzes_generated INTEGER DEFAULT 0,
    quizzes_taken INTEGER DEFAULT 0,
    documents_uploaded INTEGER DEFAULT 0,
    api_requests_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date)
);

-- ============================================
-- SOCIAL FEATURES
-- ============================================

-- Leaderboards table
CREATE TABLE IF NOT EXISTS leaderboards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category TEXT NOT NULL, -- 'overall', 'games', 'quizzes', 'learning'
    score BIGINT DEFAULT 0,
    rank INTEGER,
    period TEXT DEFAULT 'all_time', -- 'daily', 'weekly', 'monthly', 'all_time'
    period_start DATE,
    period_end DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, category, period, period_start)
);

-- User friendships
CREATE TABLE IF NOT EXISTS user_friendships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    friend_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'blocked'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, friend_id),
    CHECK (user_id != friend_id)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Session indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

-- Game indexes
CREATE INDEX IF NOT EXISTS idx_game_states_user_id ON game_states(user_id);
CREATE INDEX IF NOT EXISTS idx_game_states_case_id ON game_states(case_id);
CREATE INDEX IF NOT EXISTS idx_game_states_active ON game_states(is_active);
CREATE INDEX IF NOT EXISTS idx_game_checkpoints_user_id ON game_checkpoints(user_id);
CREATE INDEX IF NOT EXISTS idx_game_checkpoints_game_state_id ON game_checkpoints(game_state_id);

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
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_unlocked ON user_achievements(unlocked);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_api_requests_user_id ON api_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_api_requests_created_at ON api_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_api_requests_endpoint ON api_requests(endpoint);
CREATE INDEX IF NOT EXISTS idx_game_creation_log_user_id ON game_creation_log(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_generation_log_user_id ON quiz_generation_log(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics(date);

-- Leaderboard indexes
CREATE INDEX IF NOT EXISTS idx_leaderboards_category_period ON leaderboards(category, period);
CREATE INDEX IF NOT EXISTS idx_leaderboards_score ON leaderboards(score DESC);

-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_checkpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progression ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboards ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_friendships ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (users can only access their own data)
-- Note: These are basic examples. Adjust based on your security requirements.

-- Users can view and update their own data
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Sessions policies
CREATE POLICY "Users can view own sessions" ON user_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions" ON user_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Game states policies
CREATE POLICY "Users can view own game states" ON game_states
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own game states" ON game_states
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own game states" ON game_states
    FOR UPDATE USING (auth.uid() = user_id);

-- Similar policies for other tables...
-- (Add more specific policies as needed for your use case)

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

-- Function to clean up expired Pinecone indexes
CREATE OR REPLACE FUNCTION cleanup_expired_pinecone_indexes()
RETURNS void AS $$
BEGIN
    UPDATE documents
    SET pinecone_index_name = NULL,
        pinecone_index_expires_at = NULL
    WHERE pinecone_index_expires_at < NOW();
END;
$$ language 'plpgsql';

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

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert default achievements
INSERT INTO achievement_definitions (id, name, description, icon, category, points, rarity, criteria) VALUES
('first_steps', 'First Steps', 'Complete your first quest', '🏃', 'game', 10, 'common', '{"type": "quests_completed", "value": 1}'),
('quiz_master', 'Quiz Master', 'Score 90% or higher on 5 quizzes', '🧠', 'quiz', 50, 'rare', '{"type": "high_scores", "count": 5, "threshold": 90}'),
('dedicated_learner', 'Dedicated Learner', 'Study for 10 hours total', '📚', 'learning', 100, 'epic', '{"type": "learning_hours", "value": 10}'),
('game_champion', 'Game Champion', 'Complete 50 games', '🏆', 'game', 200, 'legendary', '{"type": "games_completed", "value": 50}'),
('perfect_score', 'Perfect Score', 'Score 100% on a quiz', '⭐', 'quiz', 75, 'rare', '{"type": "perfect_score", "value": 1}'),
('social_butterfly', 'Social Butterfly', 'Add 10 friends', '👥', 'social', 50, 'rare', '{"type": "friends_count", "value": 10}'),
('top_leaderboard', 'Top of the Leaderboard', 'Reach #1 on any leaderboard', '👑', 'social', 500, 'legendary', '{"type": "leaderboard_rank", "value": 1}'),
('document_expert', 'Document Expert', 'Upload and process 20 documents', '📄', 'learning', 100, 'epic', '{"type": "documents_uploaded", "value": 20}')
ON CONFLICT (id) DO NOTHING;

