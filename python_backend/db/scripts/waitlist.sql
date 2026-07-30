-- =============================================================================
-- Stud Database - Waitlist
-- =============================================================================
-- Public marketing signup: "notify me when it launches / I'd pay for this".
-- Run this script in Supabase SQL Editor or via psql. Idempotent.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS waitlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    note TEXT,
    source_page TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_waitlist_created_at ON waitlist(created_at);
