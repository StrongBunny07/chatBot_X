# ChatBot X — Startup Commands

## 1. Start Ollama (DeepSeek R1)

```bash
# Check if Ollama is running
curl http://localhost:11434/

# If not running, start the service
sudo systemctl start ollama

# Pull model (first time only)
ollama pull deepseek-r1:1.5b

# List downloaded models
ollama list
```

## 2. Start Django Backend

```bash
cd backend
python3 manage.py runserver 8000
```

- API available at: **http://localhost:8000**
- Chat endpoint: `POST http://localhost:8000/api/chat/`

## 3. Start React Frontend

```bash
cd frontend
npm run dev
```

- UI available at: **http://localhost:3000** (or 3001 if 3000 is in use)

## 4. Open in Browser

```
http://localhost:3000
```

---

## Quick Start (All at once)

Open 3 terminals and run:

```bash
# Terminal 1 — Ollama (usually auto-started as systemd service)
sudo systemctl start ollama

# Terminal 2 — Django
cd backend && python3 manage.py runserver 8000

# Terminal 3 — React
cd frontend && npm run dev
```

---

## Test Ollama Directly

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "deepseek-r1:1.5b",
  "messages": [{"role": "user", "content": "hello"}],
  "stream": false
}'
```

## Test Django API Directly

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'
```

---

## Stop Services

```bash
# Stop Ollama
sudo systemctl stop ollama

# Stop Django — Ctrl+C in its terminal

# Stop React — Ctrl+C in its terminal
```

---

## Useful Commands

```bash
# Check what's running on ports
lsof -i :8000    # Django
lsof -i :3000    # React
lsof -i :11434   # Ollama

# Check Ollama service status
sudo systemctl status ollama

# Upgrade to larger model later
ollama pull deepseek-r1:8b
```
