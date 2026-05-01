# Stud Database

## Overview

This directory contains the database initialization script for the Stud application. All tables, indexes, triggers, and seed data are defined in a single script.

## Setup

### Run in Supabase SQL Editor

1. Open your Supabase project dashboard
2. Go to **SQL Editor**
3. Copy the contents of `scripts/init_db.sql`
4. Paste and run

### Run via psql

```bash
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres" -f db/scripts/init_db.sql
```

## Script: `init_db.sql`

**Single source of truth** for all database objects. Idempotent (safe to run multiple times).

### Tables Created

| Category | Tables |
|----------|--------|
| **Auth & Users** | `users`, `user_sessions` |
| **Documents** | `documents`, `document_chunks` |
| **Games** | `game_states`, `game_checkpoints`, `game_statistics`, `game_creation_log`, `user_performance`, `game_previous_cases` |
| **Quizzes** | `quizzes`, `quiz_results`, `saved_quizzes`, `quiz_statistics` |
| **Learning** | `learning_chat_history`, `tutor_chat_history`, `curricula`, `study_plans`, `user_enrollments` |
| **Chat** | `game_master_chat_history`, `npc_chat_history` |
| **Progress** | `achievements`, `achievement_definitions`, `user_achievements`, `user_progression` |

### Includes

- Extensions: `uuid-ossp`, `vector` (pgvector)
- Indexes for performance
- Triggers for `updated_at`, game/quiz statistics
- Seed data: achievement definitions
