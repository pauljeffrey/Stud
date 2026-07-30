-- =============================================================================
-- Stud Database - Two-tier document library + notifications + suggestions
-- =============================================================================
-- Run in Supabase SQL Editor or via psql. Idempotent (IF NOT EXISTS / guarded
-- ALTER). Safe to re-run.
-- =============================================================================

-- 'private' = user's own upload (TTL-bound, per Phase III design).
-- 'global'  = curated, shared central-library document (never expires).
ALTER TABLE documents ADD COLUMN IF NOT EXISTS scope TEXT NOT NULL DEFAULT 'private';
CREATE INDEX IF NOT EXISTS idx_documents_scope ON documents(scope);

-- NULL = never expires (used for scope='global' documents). Previously
-- NOT NULL with a default; existing rows are untouched by this relaxation.
ALTER TABLE documents ALTER COLUMN pinecone_index_expires_at DROP NOT NULL;

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    related_id TEXT,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, read);

CREATE TABLE IF NOT EXISTS document_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_document_suggestions_status ON document_suggestions(status);
