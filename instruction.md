# chatBot_X — Project Plan & Instructions

## Overview

A full-stack AI chatbot application powered by DeepSeek R1 running locally via Ollama in Docker, with a Django REST backend and a React frontend.

---

## Architecture

```
┌──────────────────┐    HTTP :3000    ┌──────────────────┐    HTTP :8000    ┌──────────────────┐
│   React Frontend │  ──────────────► │  Django Backend   │  ──────────────► │  Ollama (Docker)  │
│   (Vite + React) │  ◄────────────── │  (REST API)       │  ◄────────────── │  DeepSeek R1      │
│                  │    JSON response │                   │   Streaming      │  Port: 11434      │
└──────────────────┘                  └──────────────────┘                  └──────────────────┘
```

**Flow:**
1. User types a message in the React frontend
2. React sends a POST request to Django API (`/api/chat/`)
3. Django forwards the message to Ollama (DeepSeek R1 model)
4. Ollama generates a response and streams it back
5. Django returns the response to React
6. React displays the AI response in the chat UI

---

## Tech Stack

| Layer       | Technology                        | Port  |
|-------------|-----------------------------------|-------|
| LLM         | DeepSeek R1 8B via Ollama (Docker)| 11434 |
| Backend     | Django 6.0 + requests library     | 8000  |
| Frontend    | React 18 + Vite                   | 3000  |
| Container   | Docker Compose                    | —     |
| Database    | SQLite (default, for chat history)| —     |

---

## Folder Structure

```
chatBot_X/
├── instruction.md              # This file — project plan
├── docker-compose.yml          # Orchestrates Ollama container
├── .gitignore                  # Git ignore rules
│
├── backend/                    # Django project
│   ├── manage.py
│   ├── requirements.txt        # Python dependencies
│   ├── backend/                # Django project settings
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   └── chat/                   # Chat app
│       ├── __init__.py
│       ├── views.py            # API endpoint: POST /api/chat/
│       ├── urls.py             # Chat URL routing
│       └── models.py           # ChatMessage model (history)
│
└── frontend/                   # React app (Vite)
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx            # React entry point
        ├── App.jsx             # Main app component
        ├── App.css             # App styles
        └── components/
            └── ChatBox.jsx     # Chat interface component
```

---

## Step-by-Step Build Plan

### Phase 1: Infrastructure Setup

**Step 1 — Docker Compose & Ollama**
- Create `docker-compose.yml` with Ollama service
- Map port 11434 for Ollama API
- Mount volume for model persistence
- Start container and pull `deepseek-r1:8b` model

**Step 2 — Verify Ollama is working**
- Test with: `curl http://localhost:11434/api/chat -d '{"model":"deepseek-r1:8b","messages":[{"role":"user","content":"hello"}]}'`

### Phase 2: Django Backend

**Step 3 — Scaffold Django project**
- `django-admin startproject backend` inside project root
- `python manage.py startapp chat` inside backend/

**Step 4 — Chat API endpoint**
- Create `POST /api/chat/` view
- Accept JSON: `{"message": "user message here"}`
- Return JSON: `{"response": "AI response here"}`

**Step 5 — Ollama integration**
- Use `requests` library to call Ollama API
- Endpoint: `http://localhost:11434/api/chat`
- Send model name + message history
- Handle streaming response

**Step 6 — CORS & Django config**
- Install `django-cors-headers`
- Allow React dev server (localhost:3000) to call API
- Configure `INSTALLED_APPS`, middleware, `CORS_ALLOWED_ORIGINS`

### Phase 3: React Frontend

**Step 7 — Scaffold React with Vite**
- `npm create vite@latest frontend -- --template react`
- Install dependencies: `npm install`
- Configure Vite proxy to Django backend

**Step 8 — Chat UI component**
- Build `ChatBox.jsx` with:
  - Message display area (scrollable)
  - Text input + send button
  - Message bubbles (user = right, AI = left)
  - Loading indicator while AI responds

**Step 9 — API integration**
- `fetch()` POST to `/api/chat/` with user message
- Display AI response in chat
- Maintain conversation history in React state

### Phase 4: Testing

**Step 10 — End-to-end test**
- Start all 3 services (Ollama, Django, React)
- Send a test message through the UI
- Verify response from DeepSeek R1

---

## Commands Reference

### Start Ollama (Docker)
```bash
docker compose up -d ollama
```

### Pull DeepSeek model (first time only)
```bash
docker exec -it ollama ollama pull deepseek-r1:8b
```

### Start Django backend
```bash
cd backend
python manage.py runserver 8000
```

### Start React frontend
```bash
cd frontend
npm run dev
```

### Start everything (Docker Compose)
```bash
docker compose up -d
```

---

## Environment Details

| Resource        | Value                  |
|-----------------|------------------------|
| OS              | Ubuntu (Linux)         |
| Python          | 3.12.3                 |
| Django          | 6.0.3                  |
| Node.js         | 18.19.1                |
| npm             | 9.2.0                  |
| Docker          | 29.3.0                 |
| Docker Compose  | v5.0.2                 |
| RAM             | 16 GB                  |
| Disk Free       | ~78 GB                 |
| GPU             | None (CPU-only)        |

---

## Estimated Disk Usage

| Component               | Size     |
|-------------------------|----------|
| Ollama Docker image     | ~1.5 GB  |
| DeepSeek R1 8B model    | ~4.9 GB  |
| Django backend + deps   | ~50 MB   |
| React frontend + deps   | ~300 MB  |
| **Total**               | **~7 GB**|

---

## Notes

- No API keys needed — everything runs locally for free
- No Anaconda needed — VS Code + terminal is sufficient
- DeepSeek R1 on CPU will be slower (~5-15 tokens/sec) but functional
- Chat history stored in SQLite (can upgrade to PostgreSQL later)
- Can swap models easily: `ollama pull mistral`, `ollama pull llama3.2`
