-- =============================================================================
-- Stud Database - Complete Initialization Script
-- =============================================================================
-- Run this script in Supabase SQL Editor or via psql to create all tables
-- and seed data required by the Stud application.
-- Idempotent: safe to run multiple times (uses IF NOT EXISTS / ON CONFLICT).
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- 1. AUTHENTICATION & USER MANAGEMENT
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    user_type TEXT,  -- 'professional' | 'student'
    profession TEXT,  -- profession (if professional) or field of study (if student)
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

-- NOTE: no longer written to or read by the app -- auth is JWT-bearer only now
-- (see api/auth.py). Left in place rather than dropped so existing deployments
-- don't need a destructive migration; safe to drop in a future cleanup pass.
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 2. DOCUMENTS (must exist before game_states - FK reference)
-- =============================================================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content TEXT,
    processed BOOLEAN DEFAULT FALSE,
    processing_status TEXT DEFAULT 'pending',
    pinecone_index_name TEXT,
    pinecone_index_created_at TIMESTAMP WITH TIME ZONE,
    pinecone_index_expires_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() + INTERVAL '2 hours'),
    chunk_count INTEGER DEFAULT 0,
    embedding_model TEXT DEFAULT 'text-embedding-3-small',
    s3_key TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 3. GAME MANAGEMENT
-- =============================================================================

CREATE TABLE IF NOT EXISTS game_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    case_id TEXT NOT NULL,
    state JSONB NOT NULL,
    scenario_type TEXT DEFAULT 'standard',
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    is_demo BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

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

CREATE TABLE IF NOT EXISTS game_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    games_created INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    games_completed INTEGER DEFAULT 0,
    total_score BIGINT DEFAULT 0,
    total_time_played INTEGER DEFAULT 0,
    average_score DECIMAL(5,2),
    highest_score INTEGER DEFAULT 0,
    last_played_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS game_creation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    game_state_id UUID REFERENCES game_states(id) ON DELETE SET NULL,
    scenario_type TEXT,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

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

CREATE TABLE IF NOT EXISTS game_previous_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID REFERENCES game_states(id) ON DELETE CASCADE,
    case_state_id TEXT NOT NULL,
    case_number INTEGER NOT NULL,
    scenario_summary TEXT,
    diagnosis TEXT,
    question_summary TEXT,
    difficulty_level TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(game_id, case_state_id)
);

-- =============================================================================
-- 4. QUIZ MANAGEMENT
-- =============================================================================

CREATE TABLE IF NOT EXISTS quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    questions JSONB NOT NULL,
    quiz_type TEXT NOT NULL,
    time_limit INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    difficulty TEXT DEFAULT 'intermediate',
    source TEXT DEFAULT 'ai_knowledge',
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quiz_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    answers JSONB NOT NULL,
    scores JSONB,
    score INTEGER NOT NULL,
    total_score DECIMAL(5,2),
    time_spent INTEGER NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS saved_quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, quiz_id)
);

CREATE TABLE IF NOT EXISTS quiz_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quizzes_taken INTEGER DEFAULT 0,
    quizzes_passed INTEGER DEFAULT 0,
    total_score BIGINT DEFAULT 0,
    average_score DECIMAL(5,2),
    highest_score INTEGER DEFAULT 0,
    total_time_spent INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- =============================================================================
-- 5. DOCUMENT CHUNKS & LEARNING
-- =============================================================================

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS learning_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 6. CHAT HISTORY (Game Master, NPC, Tutor)
-- =============================================================================

CREATE TABLE IF NOT EXISTS game_master_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID REFERENCES game_states(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    message_metadata JSONB DEFAULT '{}',
    parent_message_id UUID REFERENCES game_master_chat_history(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS npc_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID REFERENCES game_states(id) ON DELETE CASCADE,
    npc_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    message_metadata JSONB DEFAULT '{}',
    parent_message_id UUID REFERENCES npc_chat_history(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tutor_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    message_metadata JSONB DEFAULT '{}',
    parent_message_id UUID REFERENCES tutor_chat_history(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning curriculum, study plans, enrollments (see also db/scripts/learning_curriculum.sql)
CREATE TABLE IF NOT EXISTS curricula (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    difficulty_level TEXT DEFAULT 'Intermediate',
    modules JSONB NOT NULL DEFAULT '[]',
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, document_id)
);

CREATE TABLE IF NOT EXISTS study_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    curriculum_id UUID NOT NULL REFERENCES curricula(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    target_end_date DATE NOT NULL,
    daily_schedule JSONB NOT NULL DEFAULT '[]',
    pace_preference TEXT DEFAULT 'balanced',
    current_progress_percentage REAL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, curriculum_id)
);

CREATE TABLE IF NOT EXISTS user_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    curriculum_id UUID NOT NULL REFERENCES curricula(id) ON DELETE CASCADE,
    study_plan_id UUID NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_curricula_user_doc ON curricula(user_id, document_id);
CREATE INDEX IF NOT EXISTS idx_study_plans_curriculum ON study_plans(curriculum_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_user ON user_enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_document ON user_enrollments(document_id);

-- =============================================================================
-- 7. ACHIEVEMENTS & PROGRESSION
-- =============================================================================

CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID REFERENCES game_states(id) ON DELETE SET NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    value DECIMAL(10,2),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS achievement_definitions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    icon TEXT NOT NULL,
    category TEXT NOT NULL,
    points INTEGER DEFAULT 0,
    rarity TEXT DEFAULT 'common',
    criteria JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_id TEXT REFERENCES achievement_definitions(id) ON DELETE CASCADE,
    progress JSONB DEFAULT '{}',
    unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

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

-- =============================================================================
-- 8. INDEXES (ensure columns exist for pre-existing tables)
-- =============================================================================

-- Add columns if tables were created by older schema (run in Supabase SQL Editor, then reload schema cache)
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_type TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_expires TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS api_settings JSONB DEFAULT '{}';
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;
ALTER TABLE game_states ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed);
CREATE INDEX IF NOT EXISTS idx_documents_pinecone_expires ON documents(pinecone_index_expires_at);

CREATE INDEX IF NOT EXISTS idx_game_states_user_id ON game_states(user_id);
CREATE INDEX IF NOT EXISTS idx_game_states_case_id ON game_states(case_id);
CREATE INDEX IF NOT EXISTS idx_game_states_active ON game_states(is_active);
CREATE INDEX IF NOT EXISTS idx_game_states_is_demo ON game_states(is_demo);
CREATE INDEX IF NOT EXISTS idx_game_checkpoints_user_id ON game_checkpoints(user_id);
CREATE INDEX IF NOT EXISTS idx_game_checkpoints_game_state_id ON game_checkpoints(game_state_id);
CREATE INDEX IF NOT EXISTS idx_user_performance_user_id ON user_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_user_performance_game_id ON user_performance(game_id);
CREATE INDEX IF NOT EXISTS idx_previous_cases_game_id ON game_previous_cases(game_id);

CREATE INDEX IF NOT EXISTS idx_quizzes_user_id ON quizzes(user_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_created_at ON quizzes(created_at);
CREATE INDEX IF NOT EXISTS idx_quiz_results_user_id ON quiz_results(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_results_quiz_id ON quiz_results(quiz_id);
CREATE INDEX IF NOT EXISTS idx_saved_quizzes_user_id ON saved_quizzes(user_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_learning_chat_user_doc ON learning_chat_history(user_id, document_id);

CREATE INDEX IF NOT EXISTS idx_game_master_chat_user_game ON game_master_chat_history(user_id, game_id);
CREATE INDEX IF NOT EXISTS idx_game_master_chat_session ON game_master_chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_npc_chat_user_game ON npc_chat_history(user_id, game_id);
CREATE INDEX IF NOT EXISTS idx_npc_chat_npc_session ON npc_chat_history(npc_id, session_id);
CREATE INDEX IF NOT EXISTS idx_tutor_chat_user_doc ON tutor_chat_history(user_id, document_id);
CREATE INDEX IF NOT EXISTS idx_tutor_chat_session ON tutor_chat_history(session_id);

CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_game_statistics_user_id ON game_statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_statistics_user_id ON quiz_statistics(user_id);

-- Vector similarity search (pgvector)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- =============================================================================
-- 9. FUNCTIONS & TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_game_states_updated_at ON game_states;
CREATE TRIGGER update_game_states_updated_at BEFORE UPDATE ON game_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_quizzes_updated_at ON quizzes;
CREATE TRIGGER update_quizzes_updated_at BEFORE UPDATE ON quizzes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

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
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_game_stats_on_insert ON game_states;
CREATE TRIGGER update_game_stats_on_insert
    AFTER INSERT ON game_states
    FOR EACH ROW EXECUTE FUNCTION update_game_statistics();

CREATE OR REPLACE FUNCTION update_quiz_statistics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO quiz_statistics (user_id, quizzes_taken, total_score, average_score)
    VALUES (NEW.user_id, 1, NEW.score, NEW.score)
    ON CONFLICT (user_id) DO UPDATE
    SET quizzes_taken = quiz_statistics.quizzes_taken + 1,
        total_score = quiz_statistics.total_score + NEW.score,
        average_score = (quiz_statistics.total_score + NEW.score)::DECIMAL / (quiz_statistics.quizzes_taken + 1),
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_quiz_stats_on_insert ON quiz_results;
CREATE TRIGGER update_quiz_stats_on_insert
    AFTER INSERT ON quiz_results
    FOR EACH ROW EXECUTE FUNCTION update_quiz_statistics();

CREATE OR REPLACE FUNCTION cleanup_expired_documents()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM documents
    WHERE pinecone_index_expires_at < NOW() - INTERVAL '2 hours';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 10. SEED DATA (Achievement Definitions)
-- =============================================================================

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
