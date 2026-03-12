# Stud 🏥🎮

**Master Medicine Through Adventure**

Stud is a futuristic, gamified medical education platform that transforms healthcare learning into an immersive role-playing experience. Healthcare professionals embark on clinical adventures, master medical knowledge, and advance their careers through dynamic scenarios.

## ✅ Implementation Status

### Backend ✅ COMPLETE
- ✅ 4 Core AI Agents (Game World, Game Master, State Controller, NPC)
- ✅ State Models (GameState, CaseState, NPCState with CommonFields abstraction)
- ✅ API Routes (Game V2, Quiz V2, Learning, Auth, Cleanup)
- ✅ Redis Caching Layer
- ✅ Document Processor with 2-hour expiry
- ✅ Cleanup Service for expired documents
- ✅ Demo Mode Logic
- ✅ Performance Analysis System
- ✅ Achievement System

### Frontend ✅ COMPLETE
- ✅ Homepage with animated background and demo button
- ✅ Demo Page with configuration
- ✅ Mediquest Game Interface (3-column layout, collapsible sections, chat windows)
- ✅ Study Mode (document upload, PDF viewer, chat interface)
- ✅ Quiz Mode (generation, multiple choice/open-ended, scoring)
- ✅ About Page (creator info, accomplishments)
- ✅ How-to-Use Page (guides, API key instructions)
- ✅ Responsive Navigation Bar
- ✅ Futuristic Design (purple/navy/black theme)
- ✅ Animations (Framer Motion)

## 🚀 Quick Start - Running Locally

### Prerequisites

Before you begin, ensure you have:
- **Node.js 18+** installed ([Download](https://nodejs.org/))
- **Python 3.11+** installed ([Download](https://www.python.org/))
- **npm** or **yarn** package manager

### Frontend Setup (Next.js)

**The frontend is located in the `frontend` directory.**

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```
   
   This will install all required packages including:
   - Next.js 16
   - React 18
   - Tailwind CSS
   - Framer Motion
   - React PDF
   - Radix UI components
   - And more...

3. **Run the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   ```
   http://localhost:3000
   ```

   You should see the Stud homepage with animated background!

### Backend Setup (FastAPI)

1. **Navigate to backend directory:**
   ```bash
   cd python_backend
   ```

2. **Create virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   
   Create a `.env` file in the `python_backend` directory:
   ```env
   # Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SERVICE_ROLE_KEY=your_service_role_key
   SUPABASE_KEY=your_supabase_key

   # Redis Configuration (Optional for local dev)
   REDIS_URL=redis://localhost:6379

   # AI Model Configuration
   GOOGLE_API_KEY=your_google_api_key
   OPENAI_API_KEY=your_openai_api_key
   GAME_MASTER_MODEL_NAME=gemini-2.0-flash-exp

   # Optional Services
   SERPER_API_KEY=your_serper_api_key
   PINECONE_API_KEY=your_pinecone_api_key

   # Application Settings
   SECRET_KEY=your_secret_key_here
   ```

5. **Run the backend server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at: `http://localhost:8000`
   
   API documentation: `http://localhost:8000/docs`

## 📁 Project Structure

```
Stud/
├── frontend/                    # Next.js frontend (run from here)
│   ├── app/                     # Next.js app directory
│   │   ├── page.tsx            # Homepage
│   │   ├── demo/               # Demo page
│   │   ├── mediquest/          # Game mode
│   │   ├── study/              # Document chat mode
│   │   ├── quiz/               # Quiz mode
│   │   ├── about/              # About page
│   │   ├── how-to-use/         # Usage guide
│   │   ├── auth/               # Login/Register
│   │   ├── components/         # React components
│   │   │   ├── ui/            # UI components (Radix UI)
│   │   │   └── navbar.tsx     # Navigation bar
│   │   └── globals.css         # Global styles
│   ├── lib/                     # Shared utilities
│   ├── package.json            # Frontend dependencies
│   ├── next.config.mjs         # Next.js config
│   ├── tailwind.config.js      # Tailwind config
│   ├── tsconfig.json           # TypeScript config
│   └── postcss.config.mjs      # PostCSS config
├── python_backend/              # FastAPI backend
│   ├── agents/                 # AI agents
│   ├── api/                    # API routes
│   ├── models/                 # Pydantic models
│   ├── service/                # Services
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
└── README.md                   # This file
```

## 🎮 Using Stud

### 1. Try the Demo
- Click "Try Demo" on the homepage
- Configure your demo (optional settings)
- Experience 1 test game with 3 clinical scenarios
- After demo, register for full access

### 2. Mediquest Mode
- Initialize a game with your preferred settings
- Face clinical cases with dynamic escalation
- Chat with Game Master for guidance
- Interact with NPCs for clues
- Track your performance and earn achievements

### 3. Study Mode
- Upload medical documents (PDF, DOCX, PPT, TXT, Images)
- Chat with your documents using AI
- Create quizzes from documents
- Start Mediquest adventures from documents
- Documents expire after 2 hours

### 4. Quiz Mode
- Generate quizzes from AI knowledge or documents
- Mix multiple choice and open-ended questions
- Get AI-powered scoring for open-ended answers
- Track your performance

## 🔧 Configuration

### Frontend Environment Variables

Create a `.env.local` file in the `frontend` directory:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase (if using client-side)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Backend Environment Variables

See `.env` setup in Backend Setup section above.

## 🐛 Troubleshooting

### Frontend Issues

**Issue: `npm install` fails**
- Solution: Clear npm cache: `npm cache clean --force`
- Try: Delete `node_modules` and `package-lock.json`, then reinstall

**Issue: Port 3000 already in use**
- Solution: Use a different port: `npm run dev -- -p 3001`

**Issue: Module not found errors**
- Solution: Ensure you're in the `frontend` directory
- Run `npm install` again

**Issue: Tailwind styles not applying**
- Solution: Check `tailwind.config.js` includes correct paths
- Restart dev server

### Backend Issues

**Issue: Import errors**
- Solution: Ensure virtual environment is activated
- Check Python version: `python --version` (should be 3.11+)

**Issue: Database connection errors**
- Solution: Verify Supabase credentials in `.env`
- Check Supabase project is active

**Issue: Redis connection errors**
- Solution: Redis is optional for local dev
- Backend will work without Redis (caching disabled)

## 📚 API Endpoints

### Game API (`/api/game/`)
- `POST /initialize` - Initialize new game
- `POST /master-chat` - Chat with game master (streaming)
- `POST /npc-chat` - Chat with NPCs (streaming)
- `POST /update-state` - Update case state
- `POST /use-clue` - Use clue (triggers penalty)
- `POST /submit-answer` - Submit answer and get performance
- `GET /{game_id}` - Get game state
- `DELETE /{game_id}` - Delete game

### Quiz API (`/api/quiz/`)
- `POST /generate` - Generate quiz
- `POST /submit` - Submit quiz answers
- `POST /score-open` - Score open-ended answer

### Learning API (`/api/learning/`)
- `POST /upload` - Upload document
- `POST /chat` - Chat with document (streaming)
- `DELETE /documents/{id}` - Delete document

## 🎨 Design System

### Colors
- **Primary Purple**: `#8B5CF6`
- **Navy Blue**: `#1E3A8A`
- **Black**: `#000000`
- **White**: `#FFFFFF`

### Typography
- **Font**: Inter (from Google Fonts)
- **Headings**: Bold, gradient text effects
- **Body**: Regular weight, gray-300 for secondary text

## 🚀 Deployment

### Frontend (Vercel)
1. Push code to GitHub
2. Import project in Vercel
3. Set root directory to `frontend`
4. Set environment variables
5. Deploy

### Backend (Railway/Render)
1. Connect GitHub repository
2. Set root directory to `python_backend`
3. Set environment variables
4. Deploy Python backend
5. Update frontend API URL

## 📝 Development Commands

### Frontend (from `frontend` directory)
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Backend (from `python_backend` directory)
```bash
cd python_backend
uvicorn main:app --reload              # Development server
uvicorn main:app --host 0.0.0.0 --port 8000  # Production server
```

## 👨‍💻 Creator

**Dr. Jeffrey Otoibhi**

Stud is created by Dr. Jeffrey Otoibhi, a medical professional passionate about revolutionizing healthcare education through technology and gamification.

## 📄 License

Proprietary - All rights reserved

---

## ✅ Quick Start Checklist

Before running, verify:
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Navigate to `frontend` directory
- [ ] Run `npm install` in `frontend` directory
- [ ] Run `npm run dev` in `frontend` directory
- [ ] Open http://localhost:3000

**Ready to run!** Navigate to `frontend` directory and run `npm run dev`. 🚀
