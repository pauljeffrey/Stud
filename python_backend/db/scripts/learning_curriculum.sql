-- Learning curriculum, study plans, enrollments (run after core schema)
-- Idempotent

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
