# Stud - Core Features

## Overview

Stud is an immersive, gamified medical education platform that combines AI-powered learning with engaging gameplay mechanics. The platform offers three main modes: Mediquest (interactive clinical scenarios), Quiz Mode (knowledge assessment), and Learning (document-based study).

## Key Features

### 🎮 Mediquest Game Mode

**Interactive Clinical Adventure Game**

- **Dynamic Game Worlds**: AI-generated immersive medical environments based on user-selected or randomized configurations
  - Profession selection (Doctor, Nurse, Physiotherapist, etc.)
  - Clinical settings (Emergency, ICU, Outpatient, etc.)
  - Historical eras and geographical contexts
  - Economic and resource constraints

- **Multi-Agent Architecture**:
  - **Game World Agent**: Creates comprehensive, immersive game worlds
  - **Game Master Agent**: Generates 20-50 unique clinical cases per adventure, manages achievements, and orchestrates game flow
  - **State Controller Agent**: Dynamically escalates/de-escalates cases based on user performance (5-15 changes per case)
  - **NPC Agent**: Non-playable characters that help users identify symptoms and reach diagnoses
  - **Dice roll**: Applies escalation/de-escalation based on a 0-10 roll (when enabled)

- **Progressive Difficulty**: Cases adapt based on user performance
- **Achievement System**: Career growth, promotions, financial rewards, certifications
- **Real-time Case Evolution**: Clinical cases change dynamically as users interact
- **Performance Tracking**: Detailed analysis of strengths and weaknesses per case

### 📝 Quiz Mode

**Comprehensive Knowledge Assessment**

- **Question Types**:
  - Multiple choice questions (4 options)
  - Open-ended/theory questions with AI-powered scoring
  - Configurable mix of both types

- **Question Sources**:
  - AI model's knowledge base
  - User-uploaded documents
  - Internet search integration (for current medical guidelines)

- **Features**:
  - Time-limited quizzes
  - Real-time progress tracking
  - Detailed explanations for answers
  - Performance analytics
  - Quiz history and statistics

### 📚 Learning Mode (Document Chat)

**AI-Powered Document Study**

- **Document Support**:
  - PDF, DOCX, PPT, TXT, Images
  - Automatic text extraction and processing
  - Document preview in split-screen view

- **RAG (Retrieval-Augmented Generation)**:
  - Document chunking and embedding
  - Vector similarity search (pgvector/Pinecone)
  - Context-aware responses based on document content
  - Source citations

- **Features**:
  - Split-screen document viewer and chat
  - Persistent chat history
  - Temporary storage (2-hour expiry for free tier)
  - Seamless document-to-quiz conversion
  - Document-to-Mediquest scenario generation

### 👤 User Management

**Comprehensive User Profiles**

- User authentication (JWT-based)
- Profile management (profession, bio, avatar)
- Statistics tracking:
  - Games created/completed
  - Quiz scores and averages
  - Learning hours
  - Experience points and levels
- Achievement tracking
- Recent activities dashboard

### 🎯 Gamification Elements

- **Level System**: Experience points and leveling
- **Achievements**: Unlockable badges and rewards
- **Progress Tracking**: Visual progress indicators
- **Leaderboards**: Competitive rankings (future feature)
- **Social Features**: Friends and sharing (future feature)

## Technical Architecture

### Backend Stack

- **Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL with pgvector)
- **Cache**: Redis (for sessions and fast data access)
- **AI Models**: 
  - Google Gemini (default)
  - OpenAI GPT models
  - User-provided API keys supported

### Agent System

All agents inherit from `BaseAgent` and follow a consistent pattern:
- Model initialization via helper functions
- Reinitialization support for dynamic model switching
- Global instance pattern for singleton access

### State Management

- **GameState**: Main game state container
- **CaseState**: Clinical case scenarios
- **NPCState**: Non-playable character states
- **GameWorldModel**: World configuration and description
- **PerformanceAnalysis**: User performance metrics

### Data Storage

- **Supabase**: Persistent data (users, games, quizzes, documents)
- **Redis**: Temporary cache (sessions, active games, chat history)
- **Pinecone/pgvector**: Vector embeddings for document search

## API Structure

### Authentication
- JWT-based authentication
- Session management
- Password reset functionality

### Game Endpoints
- `/game/initialize` - Start new game
- `/game/master-chat` - Chat with game master
- `/game/npc-chat` - Chat with NPCs
- `/game/update-state` - Update case state
- `/game/submit-answer` - Submit answers
- `/game/dice-effect` - Apply dice roll effects
- `/game/save-checkpoint` - Save game progress

### Quiz Endpoints
- `/quiz/generate` - Generate quiz
- `/quiz/submit` - Submit quiz answers
- `/quiz/score-open-ended` - Score open-ended questions

### Learning Endpoints
- `/learning/upload` - Upload document
- `/learning/chat` - Chat with document
- `/learning/create-quiz` - Generate quiz from document
- `/learning/create-quest` - Generate Mediquest from document

### User Endpoints
- `/user/stats` - Get user statistics
- `/user/recent-games` - Get recent games
- `/user/recent-quizzes` - Get recent quizzes
- `/user/recent-activities` - Get all recent activities

## Pricing Tiers

### Basic Tier (₦5,000)
- Limited games per month
- Basic quiz features
- Document upload (2-hour expiry)
- User-provided API keys required

### Premium Tier (₦15,000)
- Unlimited games
- Advanced quiz features
- Extended document storage
- Priority support
- API keys optional (uses platform keys)

### Enterprise Tier (₦50,000)
- All Premium features
- Custom integrations
- Dedicated support
- Advanced analytics
- White-label options

## Security & Privacy

- JWT token-based authentication
- Password hashing (bcrypt)
- Row-level security (RLS) policies
- API key encryption (not stored in backend)
- Temporary document storage with automatic cleanup
- Rate limiting support

## Future Enhancements

- Social features (friends, sharing)
- Leaderboards and competitions
- Mobile app support
- Offline mode
- Advanced analytics dashboard
- Custom achievement creation
- Multiplayer game modes
- Integration with medical databases
