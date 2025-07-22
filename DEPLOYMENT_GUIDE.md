# MediQuest Deployment Guide

This guide provides step-by-step instructions for deploying MediQuest locally and in production on AWS/GCP.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Environment Variables](#environment-variables)
4. [Database Setup](#database-setup)
5. [Running Locally](#running-locally)
6. [Production Deployment](#production-deployment)
7. [AWS Deployment](#aws-deployment)
8. [GCP Deployment](#gcp-deployment)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Node.js 18+ and npm/yarn
- Python 3.11+
- Git
- Docker (for containerized deployment)

### Required Accounts
- Supabase account (for database)
- Google Cloud account (for Gemini API)
- AWS/GCP account (for production deployment)
- Redis Cloud account (optional, for caching)

## Local Development Setup

### 1. Clone the Repository
\`\`\`bash
git clone https://github.com/your-username/mediquest.git
cd mediquest
\`\`\`

### 2. Frontend Setup
\`\`\`bash
# Install dependencies
npm install

# or with yarn
yarn install
\`\`\`

### 3. Backend Setup
\`\`\`bash
cd python-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
\`\`\`

## Environment Variables

### Frontend (.env.local)
Create a `.env.local` file in the root directory:

\`\`\`env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Backend URL
PYTHON_BACKEND_URL=http://localhost:8000

# Redis (optional)
REDIS_URL=your_redis_url
\`\`\`

### Backend (.env)
Create a `.env` file in the `python-api` directory:

\`\`\`env
# AI Model Configuration
MODEL_NAME=gemini-2.0-flash
MODEL_API_KEY=your_gemini_api_key

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Database Configuration (if using direct PostgreSQL)
DATABASE_URL=your_postgresql_connection_string

# Redis Configuration
REDIS_URL=your_redis_url

# Other APIs
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=your_pinecone_index

# Logging
LOG_LEVEL=INFO
\`\`\`

## Database Setup

### 1. Supabase Setup
1. Go to [Supabase](https://supabase.com) and create a new project
2. Get your project URL and API keys from the project settings
3. Run the following SQL to create the required tables:

\`\`\`sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  profession TEXT NOT NULL,
  age INTEGER,
  api_settings JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Game states table
CREATE TABLE game_states (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  case_id TEXT NOT NULL,
  state JSONB NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Checkpoints table
CREATE TABLE checkpoints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  checkpoint_id TEXT NOT NULL,
  state JSONB NOT NULL,
  description TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat history table
CREATE TABLE chat_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  case_id TEXT NOT NULL,
  message JSONB NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documents table for learning module
CREATE TABLE documents (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  content TEXT,
  processed BOOLEAN DEFAULT FALSE,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quizzes table
CREATE TABLE quizzes (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  questions JSONB NOT NULL,
  time_limit INTEGER NOT NULL,
  total_questions INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quiz results table
CREATE TABLE quiz_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  quiz_id TEXT REFERENCES quizzes(id),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  answers JSONB NOT NULL,
  score INTEGER NOT NULL,
  time_spent INTEGER NOT NULL,
  completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User achievements table
CREATE TABLE achievements (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  achievement_id TEXT NOT NULL,
  earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE achievements ENABLE ROW LEVEL SECURITY;

-- Create policies (basic examples - customize based on your needs)
CREATE POLICY "Users can view own data" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (auth.uid() = id);
\`\`\`

### 2. API Keys Setup

#### Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key
5. Copy the API key to your environment variables

#### Redis Setup (Optional)
1. Go to [Redis Cloud](https://redis.com/try-free/)
2. Create a free account and database
3. Get the connection URL
4. Add to your environment variables

## Running Locally

### 1. Start the Backend
\`\`\`bash
cd python-api
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### 2. Start the Frontend
\`\`\`bash
# In the root directory
npm run dev
# or
yarn dev
\`\`\`

### 3. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Production Deployment

### Docker Setup

#### Frontend Dockerfile
\`\`\`dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN \
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
  elif [ -f package-lock.json ]; then npm ci; \
  elif [ -f pnpm-lock.yaml ]; then yarn global add pnpm && pnpm i --frozen-lockfile; \
  else echo "Lockfile not found." && exit 1; \
  fi

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN yarn build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
\`\`\`

#### Backend Dockerfile
\`\`\`dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
\`\`\`

#### Docker Compose
\`\`\`yaml
version: '3.8'

services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY}
      - PYTHON_BACKEND_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./python-api
    ports:
      - "8000:8000"
    environment:
      - MODEL_NAME=${MODEL_NAME}
      - MODEL_API_KEY=${MODEL_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
    volumes:
      - ./python-api:/app
\`\`\`

## AWS Deployment

### Using AWS App Runner

#### 1. Prepare apprunner.yaml
\`\`\`yaml
version: 1.0
runtime: nodejs18
build:
  commands:
    build:
      - npm install
      - npm run build
run:
  runtime-version: 18
  command: npm start
  network:
    port: 3000
    env: PORT
  env:
    - name: NODE_ENV
      value: production
\`\`\`

#### 2. Deploy Steps
1. Push your code to GitHub
2. Go to AWS App Runner console
3. Create a new service
4. Connect to your GitHub repository
5. Configure build settings
6. Set environment variables
7. Deploy

### Using AWS ECS with Fargate

#### 1. Build and Push Docker Images
\`\`\`bash
# Build and tag images
docker build -t mediquest-frontend .
docker build -t mediquest-backend ./python-api

# Tag for ECR
docker tag mediquest-frontend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/mediquest-frontend:latest
docker tag mediquest-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/mediquest-backend:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mediquest-frontend:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mediquest-backend:latest
\`\`\`

#### 2. Create ECS Task Definition
\`\`\`json
{
  "family": "mediquest-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/mediquest-frontend:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PYTHON_BACKEND_URL",
          "value": "http://localhost:8000"
        }
      ]
    },
    {
      "name": "backend",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/mediquest-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MODEL_API_KEY",
          "value": "your-api-key"
        }
      ]
    }
  ]
}
\`\`\`

## GCP Deployment

### Using Google Cloud Run

#### 1. Deploy Backend
\`\`\`bash
cd python-api

# Build and deploy
gcloud run deploy mediquest-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MODEL_NAME=gemini-2.0-flash,MODEL_API_KEY=your-api-key
\`\`\`

#### 2. Deploy Frontend
\`\`\`bash
# Build and deploy
gcloud run deploy mediquest-frontend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PYTHON_BACKEND_URL=https://mediquest-backend-xxx.run.app
\`\`\`

### Using Google Kubernetes Engine (GKE)

#### 1. Create Kubernetes Manifests

**deployment.yaml**
\`\`\`yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mediquest-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mediquest-frontend
  template:
    metadata:
      labels:
        app: mediquest-frontend
    spec:
      containers:
      - name: frontend
        image: gcr.io/your-project/mediquest-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: PYTHON_BACKEND_URL
          value: "http://mediquest-backend-service:8000"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mediquest-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mediquest-backend
  template:
    metadata:
      labels:
        app: mediquest-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/your-project/mediquest-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: gemini-api-key
\`\`\`

**service.yaml**
\`\`\`yaml
apiVersion: v1
kind: Service
metadata:
  name: mediquest-frontend-service
spec:
  selector:
    app: mediquest-frontend
  ports:
  - port: 80
    targetPort: 3000
  type: LoadBalancer
---
apiVersion: v1
kind: Service
metadata:
  name: mediquest-backend-service
spec:
  selector:
    app: mediquest-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
\`\`\`

#### 2. Deploy to GKE
\`\`\`bash
# Create cluster
gcloud container clusters create mediquest-cluster \
  --zone us-central1-a \
  --num-nodes 3

# Get credentials
gcloud container clusters get-credentials mediquest-cluster --zone us-central1-a

# Create secrets
kubectl create secret generic api-keys \
  --from-literal=gemini-api-key=your-api-key

# Deploy
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
\`\`\`

## Monitoring and Logging

### Application Monitoring
```python
# Add to main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    return response
