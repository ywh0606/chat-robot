# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Chat Robot — a web-based chat application with a Python/FastAPI backend and a single-page HTML frontend. The backend proxies requests to a MiMo (Xiaomi) LLM API and optionally performs web searches via SerpAPI using function calling.

## Commands

### Run the server
```bash
cd backend && python main.py
```
Server starts on http://localhost:8000. The frontend is served as static files from `frontend/`.

PowerShell restart helper (kills port 8000, relaunches):
```powershell
.\restart_server.ps1
```

### Install dependencies
```bash
pip install -r backend/requirements.txt
```

### Run tests
```bash
cd backend && pytest
```
Run a single test file:
```bash
cd backend && pytest test_chat.py -v
```
Tests use `unittest.mock` to mock HTTP calls to the MiMo API and SerpAPI — no live API keys needed for tests.

## Architecture

**Backend** (`backend/main.py`) — single-file FastAPI app:
- `POST /api/chat` — non-streaming chat with function-calling support
- `POST /api/chat/stream` — SSE streaming chat (primary UI endpoint)
- `POST /api/search` — direct SerpAPI search proxy
- `GET /health` — health check
- The LLM uses OpenAI-compatible function calling with a `web_search` tool. The flow: first API call → if LLM requests tool → execute SerpAPI search → second API call with tool result → final response.
- Environment config via `.env` (see `backend/.env.example`): `MIMO_API_KEY`, `MIMO_BASE_URL`, `MIMO_MODEL`, `SERPAPI_KEY`.

**Frontend** (`frontend/index.html`) — single HTML file with inline CSS/JS:
- Uses the streaming endpoint (`/api/chat/stream`) by default
- Renders AI responses as Markdown via `marked.js`
- No build step or framework

**OpenSpec** (`openspec/`) — spec-driven change management configuration (schema: spec-driven).

## Key Conventions

- Python 3.13+ (based on `__pycache__` bytecode version)
- Tests live alongside source in `backend/`, prefixed with `test_`
- All API communication is async (`httpx.AsyncClient`)
- Chinese is the primary language for UI text and code comments
