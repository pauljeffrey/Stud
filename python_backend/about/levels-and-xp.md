# Levels and Experience Points (XP)

## How It Works

### Storage
- **Table**: `user_progression`
- **Fields**: `level`, `experience_points`, `total_quests_completed`, `total_quizzes_completed`, `total_learning_hours`

### Formula
- **XP to next level**: `(current_level × 1000) - experience_points`
  - Level 1: 0–1000 XP needed
  - Level 2: 1000–2000 XP (1000 more)
  - Level 3: 2000–3000 XP, etc.
- **Progress bar**: `experience_points / (experience_points + xp_to_next_level) × 100`

### Current State
- On registration, users get `level: 1`, `experience_points: 0`
- **XP is awarded** when completing games and quizzes:
  - Game case completion (`game_v2.py` submit_answer): +50–100 XP (based on performance score 0–10)
  - Quiz completion (`quiz.py` submit_quiz): +10–50 XP (based on total_score 0–100)
- **Not yet implemented**: Study session XP (+5 XP per 10 minutes)

### XP Awards (implemented)
- Complete a game case: +50–100 XP (based on performance score)
- Complete a quiz: +10–50 XP (based on score)
