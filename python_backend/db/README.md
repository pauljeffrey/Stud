# Database Schema Documentation

## Overview
This directory contains SQL scripts for creating all database tables required by the Stud application.

## Schema Files

### `complete_schema.sql`
**Complete database schema** - Contains all tables referenced in the application:
- All tables from `database_schema.sql` (original schema)
- All tables from `database_schema_v2.sql` (updated schema)
- All tables referenced in `api/user.py`
- All tables referenced in `api/game_v2.py`

### Tables Included

#### Authentication & User Management
- `users` - User accounts and profiles
- `user_sessions` - Active user sessions

#### Game Management
- `game_states` - Current game states (with is_demo flag)
- `game_checkpoints` - Saved game checkpoints
- `game_statistics` - User game statistics
- `game_creation_log` - Game creation tracking
- `user_performance` - Performance analysis per clinical case

#### Quiz Management
- `quizzes` - Quiz definitions
- `quiz_results` - Quiz attempt results
- `saved_quizzes` - User's favorite quizzes
- `quiz_statistics` - User quiz statistics

#### Learning & Documents
- `documents` - Uploaded documents (with expiry)
- `document_chunks` - Document chunks with embeddings (pgvector)
- `learning_chat_history` - Chat history for document learning

#### Achievements & Progression
- `achievements` - User achievements
- `achievement_definitions` - Achievement definitions
- `user_achievements` - User achievement progress tracking
- `user_progression` - User level and XP

## Usage

To set up the database, run:

```sql
-- Run the complete schema
\i db/scripts/complete_schema.sql
```

Or execute the SQL file directly in your PostgreSQL/Supabase database.

## Notes

- All tables include proper indexes for performance
- Foreign key constraints ensure data integrity
- Triggers automatically update `updated_at` timestamps
- Functions handle statistics updates automatically
- RLS (Row Level Security) policies can be added as needed
