# Quiz Mode Workflow

## Overview

Quiz Mode allows users to test their medical knowledge through AI-generated quizzes. Quizzes can be created from AI knowledge, user-uploaded documents, or a combination of both. The system supports both multiple-choice and open-ended questions with AI-powered scoring.

## Architecture Components

### Agents
- **Quiz Agent** - Generates quiz questions
- **Scoring Agent** - Scores open-ended answers

### Models
- `Quiz` - Quiz structure with questions
- `QuizQuestion` - Individual question model
- `OpenEndedAnswer` - Scoring result for open-ended questions

## Workflow: Quiz Generation

### 1. User Request
```
POST /api/quiz/generate
{
  "quiz_type": "cardiology",
  "num_questions": 10,
  "num_multiple_choice": 7,
  "num_open_ended": 3,
  "time_limit": 600,
  "source": "ai_knowledge",  // or "document"
  "document_id": "uuid",  // if source is "document"
  "model_name": "gemini-2.5-pro",
  "api_key": "user_api_key",
  "provider": "google",
  "use_internet": true
}
```

### 2. Backend Processing

**Step 1: Validate Request**
- Check required fields
- Validate question counts
- Verify document exists (if document-based)

**Step 2: Get Document Context (if applicable)**
```python
if source == "document":
    document = db_service.get_document(document_id)
    context = document.get("content", "")[:5000]  # First 5k chars
else:
    context = None
```

**Step 3: Initialize Quiz Agent**
```python
quiz_agent_instance = get_quiz_agent(
    model_name=model_name,
    api_key=api_key,
    provider=provider,
    use_internet=use_internet
)
quiz_agent = quiz_agent_instance.agent
```

**Step 4: Generate Quiz**
```python
quiz = await generate_quiz(
    quiz_type=quiz_type,
    num_questions=num_questions,
    time_limit=time_limit,
    context=context,
    source=source,
    num_multiple_choice=num_multiple_choice,
    num_open_ended=num_open_ended,
    model_name=model_name,
    api_key=api_key,
    provider=provider,
    use_internet=use_internet
)
```

**Agent Processing**:
1. Build prompt with specifications
2. If `use_internet=True`, agent can search for current information
3. Generate questions based on type distribution
4. For multiple choice: 4 options, 1 correct answer
5. For open-ended: Detailed question requiring explanation
6. Include explanations for all answers

**Step 5: Process Quiz Structure**
```python
quiz.id = f"quiz_{uuid.uuid4()}"
quiz.timeLimit = time_limit
quiz.totalQuestions = len(quiz.questions)
quiz.source = source

# Assign IDs to questions
for i, question in enumerate(quiz.questions):
    question.question_id = f"q_{i+1}_{uuid.uuid4()}"
```

**Step 6: Save to Database**
```python
db_service.create_quiz(
    user_id=user_id,
    title=f"{quiz_type} Quiz",
    questions=[q.model_dump() for q in quiz.questions],
    quiz_type="mixed",  # or "multiple_choice", "open_ended"
    time_limit=time_limit,
    total_questions=len(quiz.questions),
    source=source,
    document_id=document_id if source == "document" else None
)
```

**Step 7: Cache in Redis**
```python
await redis_service.cache_quiz_session(
    quiz_id=quiz.id,
    quiz_data=quiz.model_dump(),
    ttl=1800  # 30 minutes
)
```

### 3. Response
```json
{
  "success": true,
  "quiz": {
    "id": "quiz_uuid",
    "title": "Cardiology Quiz",
    "questions": [
      {
        "question_id": "q_1_uuid",
        "question": "What is the most common cause of...",
        "type": "multiple_choice",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "B",
        "explanation": "..."
      },
      {
        "question_id": "q_2_uuid",
        "question": "Explain the pathophysiology of...",
        "type": "open_ended",
        "correct_answer": "Model answer...",
        "explanation": "..."
      }
    ],
    "timeLimit": 600,
    "totalQuestions": 10,
    "source": "ai_knowledge"
  }
}
```

## Workflow: Taking a Quiz

### 1. Start Quiz Session
```
POST /api/quiz/start
{
  "quiz_id": "quiz_uuid",
  "user_id": "user_uuid"
}
```

**Flow**:
1. Get quiz from database or Redis cache
2. Initialize quiz progress in Redis:
   ```python
   await redis_service.cache_quiz_progress(
       user_id=user_id,
       quiz_id=quiz_id,
       answers={},
       current_question=0,
       time_remaining=quiz.timeLimit
   )
   ```
3. Return quiz data

### 2. Submit Answer (Multiple Choice)
```
POST /api/quiz/submit-answer
{
  "quiz_id": "quiz_uuid",
  "question_id": "q_1_uuid",
  "answer": "B",
  "time_remaining": 450
}
```

**Flow**:
1. Get quiz progress from Redis
2. Validate answer format
3. Get correct answer from quiz
4. Score answer (correct = 1, incorrect = 0)
5. Update progress:
   ```python
   progress["answers"][question_id] = {
       "user_answer": answer,
       "correct": answer == correct_answer,
       "score": 1 if correct else 0
   }
   progress["current_question"] += 1
   progress["time_remaining"] = time_remaining
   ```
6. Save progress to Redis
7. Return immediate feedback

### 3. Submit Answer (Open-Ended)
```
POST /api/quiz/submit-open-ended
{
  "quiz_id": "quiz_uuid",
  "question_id": "q_2_uuid",
  "answer": "The pathophysiology involves...",
  "time_remaining": 300
}
```

**Flow**:
1. Get quiz and question
2. Get user answer
3. Score using AI:
   ```python
   scoring_result = await score_open_ended_answer(
       question=question,
       user_answer=answer,
       model_name=model_name,
       api_key=api_key,
       provider=provider
   )
   ```
4. Scoring Agent analyzes:
   - Compares with model answer
   - Generates score (0-10)
   - Identifies strengths
   - Identifies weaknesses
   - Lists correct elements
   - Lists missing elements
5. Update progress with scoring result
6. Return detailed feedback

### 4. Complete Quiz
```
POST /api/quiz/complete
{
  "quiz_id": "quiz_uuid",
  "user_id": "user_uuid"
}
```

**Flow**:
1. Get final progress from Redis
2. Calculate total score:
   ```python
   total_score = sum(
       answer["score"] for answer in progress["answers"].values()
   )
   percentage = (total_score / total_questions) * 100
   ```
3. Save quiz result:
   ```python
   db_service.create_quiz_result(
       user_id=user_id,
       quiz_id=quiz_id,
       answers=progress["answers"],
       scores={q_id: ans["score"] for q_id, ans in progress["answers"].items()},
       total_score=percentage,
       time_spent=quiz.timeLimit - progress["time_remaining"]
   )
   ```
4. Update quiz statistics:
   ```python
   stats = db_service.get_quiz_statistics(user_id)
   db_service.update_quiz_statistics(user_id, {
       "quizzes_taken": stats["quizzes_taken"] + 1,
       "total_score": stats["total_score"] + percentage,
       "average_score": (stats["total_score"] + percentage) / (stats["quizzes_taken"] + 1)
   })
   ```
5. Clear Redis cache
6. Return final results

## Workflow: Internet-Enhanced Quizzes

When `use_internet=True`:

**Agent Flow**:
1. Quiz Agent receives generation request
2. For questions requiring current info:
   - Calls `search_internet(query)` tool
   - Retrieves top 5 search results
   - Incorporates current information into question
3. Generates question with latest medical guidelines
4. Includes sources in explanation

**Example**:
```
Question: "According to 2024 guidelines, what is the recommended..."
Agent searches: "2024 medical guidelines [topic]"
Uses results to create accurate, current question
```

## Data Flow Diagram

```
User Request (Generate Quiz)
    ↓
Validate Request
    ↓
[If Document-Based] Get Document Context
    ↓
Initialize Quiz Agent (with internet tool if enabled)
    ↓
Generate Questions (AI Model)
    ↓
[If Internet Enabled] Search for Current Info
    ↓
Structure Quiz Object
    ↓
Save to Database
    ↓
Cache in Redis
    ↓
Return Quiz

User Takes Quiz
    ↓
Submit Answers
    ↓
[Multiple Choice] Immediate Scoring
    ↓
[Open-Ended] AI Scoring Agent
    ↓
Update Progress (Redis)
    ↓
Complete Quiz
    ↓
Calculate Final Score
    ↓
Save Results (Database)
    ↓
Update Statistics
    ↓
Return Results
```

## Scoring Algorithm

### Multiple Choice
- Correct answer: 1 point
- Incorrect answer: 0 points
- Total: Sum of all question scores

### Open-Ended Questions
- AI analyzes answer against model answer
- Score range: 0-10
- Factors considered:
  - Accuracy of key concepts
  - Completeness of explanation
  - Medical terminology usage
  - Critical thinking demonstrated
- Penalties for:
  - Significant errors
  - Missing key elements
  - Vague or incomplete answers

## Error Handling

- **Invalid Quiz ID**: Return 404 Not Found
- **Quiz Expired**: Return 400 with message
- **Answer Format Error**: Return 400 with validation details
- **Scoring Error**: Return 500 with error details
- **Rate Limiting**: Return 429 Too Many Requests

## Performance Optimizations

- Redis caching for active quiz sessions (30 min TTL)
- Batch scoring for multiple open-ended questions
- Lazy loading of quiz questions
- Connection pooling for database
- Async processing for AI operations

## Security Considerations

- User ID validation from JWT token
- Quiz ownership verification
- Time limit enforcement
- Answer validation and sanitization
- Rate limiting per user
