# Stud API Documentation

This directory contains comprehensive documentation about the Stud medical education platform.

## Documentation Files

### Core Documentation
- **[core-features.md](./core-features.md)** - Overview of all core features and capabilities
- **[README.md](./README.md)** - This file, providing an index to all documentation

### Workflow Documentation
- **[mediquest-workflow.md](./mediquest-workflow.md)** - Complete workflow for Mediquest game mode
- **[quiz-workflow.md](./quiz-workflow.md)** - Complete workflow for Quiz mode
- **[learning-workflow.md](./learning-workflow.md)** - Complete workflow for Learning/Document chat mode

## Quick Links

### Understanding the System
1. Start with [core-features.md](./core-features.md) for an overview
2. Read workflow documents for specific features you're implementing
3. Refer to API code for implementation details

### For Developers
- **Backend API**: `python_backend/api/`
- **Agents**: `python_backend/agents/`
- **Services**: `python_backend/service/`
- **Models**: `python_backend/models/`
- **Database**: `python_backend/db/scripts/`

### For API Consumers
- **Game Endpoints**: See mediquest-workflow.md
- **Quiz Endpoints**: See quiz-workflow.md
- **Learning Endpoints**: See learning-workflow.md

## Architecture Overview

### Multi-Agent System
- Game World Agent
- Game Master Agent
- State Controller Agent
- NPC Agent
- Dice Agent
- Quiz Agent
- RAG Agent

### Data Storage
- **Supabase (PostgreSQL)**: Persistent data
- **Redis**: Session cache and temporary data
- **Pinecone/pgvector**: Vector embeddings

### API Structure
- FastAPI framework
- JWT authentication
- Streaming responses for chat
- RESTful endpoints

## Getting Started

1. **Setup Database**: Run `db/scripts/complete_schema.sql`
2. **Configure Environment**: Set up `.env` with API keys
3. **Start Backend**: `docker-compose up` or `uvicorn main:app`
4. **Start Frontend**: `cd frontend && npm run dev`

## Support

For questions or issues, refer to the specific workflow documentation or check the code comments in the respective modules.
