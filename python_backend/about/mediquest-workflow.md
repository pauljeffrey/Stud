# Mediquest Game Workflow

## Overview

Mediquest is an interactive clinical adventure game where users navigate through dynamic medical scenarios. The game uses a multi-agent architecture to create immersive, educational experiences.

## Architecture Components

### Agents
1. **Game World Agent** - Creates the game world
2. **Game Master Agent** - Generates cases and manages game flow
3. **State Controller Agent** - Escalates/de-escalates cases
4. **NPC Agent** - Provides character interactions
5. **Dice Agent** - Applies random scenario effects

### State Models
- `GameState` - Main game state container
- `CaseState` - Current clinical case
- `NPCState` - Non-playable character states
- `GameWorldModel` - World configuration
- `PerformanceAnalysis` - User performance metrics

## Workflow: Game Initialization

### 1. User Request
```
POST /api/game/initialize
{
  "game_config": {
    "profession": "Doctor",
    "clinical_setting": "Emergency",
    "subject": "Cardiology",
    "era": "21st Century",
    "total_cases": 30
  },
  "is_demo": false,
  "model_name": "gemini-2.0-flash-exp",
  "api_key": "user_api_key",
  "provider": "google"
}
```

### 2. Backend Processing

**Step 1: Validate Request**
- Check demo limits (if demo mode)
- Validate game configuration
- Extract user ID from JWT token

**Step 2: Initialize Game World**
```python
game_world_agent = get_game_world_agent(model_name, api_key, provider)
game_world = await game_world_agent.create_world(game_config)
```
- Randomize any None values in config
- Generate comprehensive world description
- Set hospital, department, resources

**Step 3: Generate First Case**
```python
game_master = get_game_master_agent(model_name, api_key, provider)
case_state = await game_master._generate_clinical_case(
    game_config, case_number=1, user_id, game_world
)
```
- Create clinical scenario
- Generate question, options, answer
- Set examination findings, investigations
- Configure max_clinical_changes (5-15)

**Step 4: Create NPCs**
```python
npc_states = await game_master._create_npcs_for_case(case_state, game_world)
```
- Create Patient NPC
- Create supporting NPCs (Nurse, Specialist, etc.)
- Set personality based on condition

**Step 5: Create Game State**
```python
game_state = GameState(
    game_id=uuid4(),
    user_id=user_id,
    game_world=game_world,
    case_state=case_state,
    npc_states=npc_states,
    current_case_number=1,
    total_cases=30
)
```

**Step 6: Persist Data**
- Cache in Redis (1 hour TTL)
- Save to Supabase `game_states` table
- Log in `game_creation_log` table

### 3. Response
```json
{
  "success": true,
  "game_state": {
    "game_id": "uuid",
    "game_world": {...},
    "case_state": {...},
    "npc_states": [...],
    "current_case_number": 1,
    "total_cases": 30
  }
}
```

## Workflow: Playing the Game

### User Interactions

#### 1. Chat with Game Master
```
POST /api/game/master-chat
{
  "game_state": {...},
  "user_message": "What should I do next?",
  "model_name": "...",
  "api_key": "..."
}
```

**Flow**:
1. Parse game state from request
2. Get Game Master Agent
3. Call `chat_with_game_master(game_state, user_message)`
4. Stream response word-by-word
5. Return updated game state

#### 2. Chat with NPC
```
POST /api/game/npc-chat
{
  "game_state": {...},
  "npc_id": "npc-uuid",
  "user_message": "How are you feeling?",
  "chat_history": [...]
}
```

**Flow**:
1. Parse game state
2. Find NPC by ID from `case_state.npc`
3. Get NPC Agent
4. Call `chat_with_npc(npc_state, user_message, case_state, chat_history)`
5. Stream response
6. Update NPC clue level

#### 3. Update Case State (Automatic/Manual)
```
POST /api/game/update-state
{
  "game_state": {...},
  "time_elapsed": 120,
  "clue_used": false
}
```

**Flow**:
1. Parse game state
2. Get State Controller Agent
3. Call `update_case_state()`:
   - Check if max_changes reached
   - Generate escalation/de-escalation
   - Update case scenario, findings, investigations
   - Apply penalty if clue used
4. If max_changes reached → Handoff to Game Master
5. Update Redis cache and Supabase
6. Return updated state

#### 4. Use Clue
```
POST /api/game/use-clue
{
  "game_state": {...}
}
```

**Flow**:
1. Mark `clue_used = True` in case state
2. Call `update_case_state()` with `clue_used=True`
3. State Controller applies penalty:
   - Reduces time remaining by 60 seconds
   - Escalates case difficulty
   - Marks penalty_applied flag

#### 5. Submit Answer
```
POST /api/game/submit-answer
{
  "game_state": {...},
  "answer": "Myocardial infarction",
  "time_taken": 180
}
```

**Flow**:
1. Parse game state and answer
2. Analyze performance:
   - Compare user answer with correct answer
   - Consider time taken vs time limit
   - Apply penalty if clue used
   - Generate score (0-10)
   - Identify strengths and weaknesses
3. Create `PerformanceAnalysis`:
   ```python
   performance = PerformanceAnalysis(
       clinical_state_id=case_state.case_state_id,
       score=8.5,
       analysis="Good diagnosis...",
       strengths=["Accurate diagnosis", "Quick response"],
       weaknesses=["Could improve time management"]
   )
   ```
4. Add to `game_state.user_performance`
5. Save to `user_performance` table
6. Update Redis and Supabase
7. Return performance analysis

## Workflow: Case Completion & Handoff

### When Max Changes Reached

**Trigger**: `case_state.n_changes >= case_state.max_clinical_changes`

**Flow**:
1. Get latest performance from `user_performance` list
2. Call Game Master `handoff_from_state_controller()`:
   ```python
   game_state = await game_master.handoff_from_state_controller(
       game_state, final_performance
   )
   ```
3. Game Master processes:
   - Adds performance to history
   - Calculates average score
   - Generates achievements:
     - Promotion (if score >= 8.0)
     - Financial reward (if score >= 7.0)
     - Milestone achievements
   - Updates game world dynamically
   - Generates next case (if not at limit)
   - Creates NPCs for new case
4. Update `game_state`:
   - Increment `current_case_number`
   - Update `case_state` with new case
   - Update `npc_states`
   - Update `achievements` list
5. Save to database
6. Return updated game state

## Workflow: Dice Effects

```
POST /api/game/dice-effect
{
  "game_state": {...},
  "dice_result": 3
}
```

**Flow**:
1. Validate dice result (1-6)
2. Get Dice Agent
3. Call `generate_dice_effect(game_state, dice_result)`:
   - Dice 1-2: Complications (worsening condition)
   - Dice 3-4: Moderate changes (new symptoms)
   - Dice 5-6: Favorable (improvement)
4. Append effect to case scenario description
5. Stream response
6. Return updated game state

## Data Flow Diagram

```
User Request
    ↓
API Endpoint (game_v2.py)
    ↓
Parse Request & Validate
    ↓
Get Agent Instance
    ↓
Call Agent Method
    ↓
Agent Processes (AI Model)
    ↓
Update State Models
    ↓
Cache in Redis
    ↓
Save to Supabase
    ↓
Return Response
```

## State Transitions

```
INITIALIZE
    ↓
[Game World Created]
    ↓
[First Case Generated]
    ↓
[User Interacts]
    ↓
[State Controller Updates Case]
    ↓
[Max Changes?] → NO → [Continue Playing]
    ↓ YES
[Performance Analyzed]
    ↓
[Game Master Handoff]
    ↓
[Achievements Generated]
    ↓
[Next Case Generated]
    ↓
[Repeat until total_cases reached]
    ↓
[Game Complete]
```

## Error Handling

- **Invalid Game State**: Return 400 Bad Request
- **Agent Errors**: Return 500 with error details
- **Redis Unavailable**: Fallback to Supabase only
- **Rate Limiting**: Return 429 Too Many Requests
- **Demo Limits**: Return 400 with upgrade message

## Performance Optimizations

- Redis caching for active games (1 hour TTL)
- Lazy loading of game states
- Streaming responses for chat endpoints
- Batch operations for multiple updates
- Connection pooling for database

## Security Considerations

- JWT token validation on all endpoints
- User ID extraction from token
- Ownership verification before operations
- Rate limiting per user
- Input validation and sanitization
