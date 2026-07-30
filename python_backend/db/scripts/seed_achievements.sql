-- =============================================================================
-- Stud Database - Achievement definitions seed
-- =============================================================================
-- Static catalog of unlockable achievements. Unlock status/progress is
-- computed per-user at request time against these criteria (see
-- api/user.py get_achievements) and persisted to user_achievements once
-- unlocked. Idempotent (ON CONFLICT DO NOTHING) — safe to re-run.
-- criteria shape: {"metric": "<key>", "threshold": <number>}
-- =============================================================================

INSERT INTO achievement_definitions (id, name, description, icon, category, points, rarity, criteria) VALUES
('first_steps', 'First Steps', 'Complete your first quest', '🏃', 'game', 10, 'common', '{"metric": "games_completed", "threshold": 1}'),
('quiz_master', 'Quiz Master', 'Pass 5 quizzes', '🧠', 'quiz', 50, 'rare', '{"metric": "quizzes_passed", "threshold": 5}'),
('dedicated_learner', 'Dedicated Learner', 'Study for 10 hours total', '📚', 'learning', 100, 'epic', '{"metric": "total_learning_hours", "threshold": 10}'),
('game_champion', 'Game Champion', 'Complete 50 games', '🏆', 'game', 200, 'legendary', '{"metric": "games_completed", "threshold": 50}'),
('perfect_score', 'Perfect Score', 'Score 100% on a quiz', '⭐', 'quiz', 75, 'rare', '{"metric": "quiz_highest_score", "threshold": 100}'),
('curious_mind', 'Curious Mind', 'Upload your first study document', '📄', 'learning', 15, 'common', '{"metric": "documents_uploaded", "threshold": 1}')
ON CONFLICT (id) DO NOTHING;
