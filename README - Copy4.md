# Stud

**Master Medicine Through Adventure**

Stud is a gamified medical education platform that turns clinical learning into an interactive adventure. Learners work through realistic cases, chat with AI characters, study their own documents, and take smart quizzes—all in one product.

---

## Table of Contents

- [Overview](#overview)
- [Key Product Decisions](#key-product-decisions)
- [How the System Is Built](#how-the-system-is-built)
- [How the AI Agents Work Together](#how-the-ai-agents-work-together)
- [Challenges & How They Were Handled](#challenges--how-they-were-handled)
- [Trade-offs](#trade-offs)
- [Quality & Testing](#quality--testing)
- [Academic & Professional Context](#academic--professional-context)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)

---

## Overview

Most medical tools are either static (PDFs, question banks) or generic chatbots. Stud sits in the middle: **structured, game-like clinical practice** with feedback, progression, and multiple ways to learn.

| Mode | What the user does | What makes it different |
|------|--------------------|------------------------|
| **Mediquest** | Play through clinical scenarios like a role-playing game | Cases change based on your answers; NPCs and a Game Master guide you |
| **Study** | Upload notes or textbooks and ask questions | Answers are grounded in *your* documents, not generic web text |
| **Quiz** | Take AI-generated tests | Mix of multiple choice and written answers with automated feedback |

---

## Key Product Decisions

### 1. Learning as a game, not a slideshow

Clinical skills improve with practice under pressure. Stud uses timers, clues, characters, achievements, and cases that get harder or easier—so learners repeat scenarios instead of memorizing once.

### 2. Several focused AI roles instead of one “do everything” bot

Each part of the product has its own AI job, similar to roles on a clinical team:

| AI role | What it does |
|---------|----------------|
| **World builder** | Creates the hospital setting, era, and context |
| **Game Master** | Writes cases, tracks progress, chats with the learner |
| **Case controller** | Makes the scenario harder or easier based on performance |
| **NPC characters** | Patients, nurses, colleagues—in-character dialogue |
| **Tutor & Quiz AI** | Document study help and test generation |

This keeps responses more reliable than asking one model to handle everything at once.

### 3. Clear data rules for game progress

Game progress (scores, case state, achievements) follows strict, validated structures before it is saved. That reduces bugs when the website and server exchange information during play.

### 4. Optional personal AI keys

Users can connect their own AI provider keys (stored encrypted). If they do not, the platform uses default models so demos and onboarding still work.

### 5. Try-before-you-register demo

Anonymous demo sessions run without full account setup. Progress is kept in fast temporary storage so new users can explore before signing up.

---

## How the System Is Built

Stud is a **web app plus API server**—a common, maintainable split:

```
  Browser (website)  ──►  API server  ──►  Database & cache
                              │
                              └──►  AI services (Gemini, OpenAI, etc.)
```

| Part | Role in plain terms |
|------|---------------------|
| **Website** | What users see: game screen, study chat, quizzes, dashboard |
| **API server** | Business logic, AI calls, login, saving progress |
| **Database** | User accounts, saved games, quizzes, uploaded files |
| **Cache** | Fast access to active game sessions |
| **AI providers** | Generate cases, chat replies, quiz questions |

**Security highlights:** Password-based login with secure tokens, encrypted storage for user API keys, and rate limiting to reduce abuse.

**Deployment:** Backend runs in Docker; frontend is built for modern hosting (e.g. Vercel).

---

## How the AI Agents Work Together

### Starting a Mediquest game

1. **World builder** creates the setting (hospital, specialty, difficulty context).
2. **Game Master** sets up the adventure and first case.
3. **Case controller** writes the clinical scenario and question.
4. **NPC builder** creates characters (patient, staff, etc.).
5. Progress is saved so the learner can continue without reloading everything.

### While playing

| Learner action | Which AI is involved |
|----------------|----------------------|
| Chat with Game Master | Game Master |
| Talk to a patient or colleague | NPC character AI |
| Use a hint | Case controller (often makes the case harder) |
| Submit an answer | Scoring AI + case controller |
| Finish a case | Game Master awards achievements and loads the next case |

### Study & Quiz modes

- **Study:** Documents are parsed, indexed, then a tutor AI answers using that content.
- **Quiz:** A dedicated quiz AI generates and grades questions from AI knowledge or uploaded material.

The Game Master coordinates the adventure; the API layer decides which AI to call for each user action.

---

## Challenges & How They Were Handled

| Challenge | Why it mattered | Approach |
|-----------|-----------------|----------|
| **Slow AI responses** | Game setup can take 15–45 seconds | Cache sessions, stream chat word-by-word, reuse init data in the browser |
| **Many steps to start a game** | Each step depends on the last | Save state early; don’t block the user while writing to the database |
| **Website and server out of sync** | Broken buttons when incomplete data was sent | Keep a full copy of game data on the server; merge carefully on each action |
| **Heavy document uploads** | Large PDFs use a lot of memory | Auto-delete temp files; process uploads in the background where possible |
| **Demo users vs registered users** | Anonymous IDs broke database saves | Store demos in cache only; full accounts use the database |

---

## Trade-offs

| Choice | Upside | Downside |
|--------|--------|----------|
| Multiple AI roles | Clearer behavior, easier to improve one part | Slower first load, more code to maintain |
| Strict game data rules | Fewer silent bugs | More care needed when updating the UI |
| User-provided AI keys | Lower cost for power users, model choice | More setup and support |
| Streaming chat | Feels responsive | Harder to handle errors mid-stream |
| Shorter AI prompts | Faster, cleaner UI text | Less detail per scenario |

---

## Quality & Testing

| Area | Status |
|------|--------|
| Mediquest (play, chat, clues, scoring) | Built and iteratively fixed |
| Study mode (upload + chat) | Built |
| Quiz mode | Built |
| Accounts, dashboard, encrypted API keys | Built |
| Demo mode | Built |

Automated tests hit a running API (`tests/ai_tests/`). Manual checks cover demo flow, login, document study, and error messages shown to users.

**Rough performance (typical):**

- Simple API calls: under a second (excluding AI)
- AI reply: a few seconds per message
- New game setup: often 15–45 seconds depending on provider

---

## Academic & Professional Context

Stud applies **serious games** and **formative assessment** ideas to medical training:

- **Situated learning** — cases happen inside a believable clinical setting, not isolated trivia.
- **Feedback loops** — each case yields a score, strengths, and areas to improve.
- **Adaptive difficulty** — scenarios evolve based on answers and time.

Built as a full-stack product combining clinical education goals with modern AI and web engineering.

Deeper technical write-ups live in `python_backend/about/` (workflows, scaling notes, document-driven game design).

---

## Tech Stack

| Layer | Tools (for recruiters who scan stacks) |
|-------|----------------------------------------|
| **Frontend** | Next.js, React, TypeScript, Tailwind CSS |
| **Backend** | Python, FastAPI |
| **AI** | Google Gemini, OpenAI, OpenRouter (pluggable) |
| **Data** | Supabase (PostgreSQL), Redis |
| **Auth & security** | JWT login, bcrypt passwords, encrypted API keys |
| **DevOps** | Docker Compose |

---

## Project Structure

```
Stud/
├── frontend/          # Website (game, study, quiz, dashboard)
├── python_backend/    # API, AI agents, database services
│   ├── agents/        # Specialized AI modules
│   ├── api/           # HTTP endpoints
│   └── about/         # Detailed design docs
└── tests/ai_tests/    # API integration tests
```

---

## Quick Start

**Prerequisites:** Node.js 18+, Python 3.11+, Docker (recommended), Supabase + AI API keys.

**Backend:**
```bash
cd python_backend
cp .env.example .env
docker-compose -f docker-compose.local.yml up
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` — API docs at `http://localhost:8000/docs`.

**Tests:**
```bash
pip install -r tests/ai_tests/requirements-ai.txt
pytest tests/ai_tests -v
```

---

## License

Proprietary — All rights reserved.
