# CLAUDE.md - BuilTPro Brain AI

## Project Overview

BuilTPro Brain AI (internally "Diriyah Brain AI") is an enterprise-grade AI-powered construction project management platform built for the USD $63 billion BuilTPro giga-project in Saudi Arabia. It combines document intelligence, BIM integration, project forecasting, and real-time monitoring.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI 0.128.0, SQLAlchemy 2.0, Celery 5.4, Alembic
- **Frontend**: React 18, Vite, Tailwind CSS, React Router 6, i18next
- **Database**: PostgreSQL 15, Redis 7, ChromaDB, FAISS
- **AI Services**: OpenAI (GPT-4), Kimi/Moonshot (kimi-k2.5), spaCy, YOLO
- **Deployment**: Docker Compose, Kubernetes (Helm), Render.com

## Development Commands

```bash
# Setup
./scripts/setup-dev-env.sh

# Backend
source .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm run dev

# Tests
pytest -q --disable-warnings --maxfail=1

# Docker
docker compose up --build

# Database
alembic upgrade head
python scripts/seed_database.py
```

## Project Structure

```
backend/
  api/          # ~60 API endpoint modules (chat, auth, forecast_engine, ifc_parser, etc.)
  app/models/   # SQLAlchemy models
  services/     # Business logic (vision.py, intent_router.py, etc.)
  connectors/   # External service connectors (factory pattern with stub fallback)
  schemas/      # Pydantic request/response schemas
  tests/        # Unit tests
frontend/
  src/components/  # Reusable React components
  src/pages/       # Page components
scripts/           # Utility scripts (Python)
mcp-servers/       # MCP server integrations
  kimi/            # Kimi AI MCP server
```

## Code Conventions

- Python target: 3.11+
- Use `from __future__ import annotations` at top of files
- `httpx` for HTTP clients (already in requirements), not `requests` for new code
- Custom exception classes per service (e.g., `VisionError`, `KimiAPIError`)
- API routers registered in `main.py` via `_iter_router_specs()`
- Connector factory pattern: `backend/connectors/factory.py` (stub/live via env)
- Pydantic `BaseSettings` for config: `backend/config.py`
- Environment variables via `.env` file (see `.env.example` for all 420+ items)

## Kimi AI Integration

### When to Use Kimi

- **Vision/Image Analysis**: Construction site photos, drawing analysis, progress verification
- **Code Generation**: Python scripts for EVM, QTO, scheduling, cost analysis
- **Document Analysis**: Contracts, specifications, RFIs with 128k context window
- **Long-context Tasks**: Use `moonshot-v1-128k` for documents exceeding 20k characters

### CLI Helper (scripts/call_kimi.py)

```bash
# Chat mode
python scripts/call_kimi.py --mode chat --prompt "What are typical EVM thresholds?"

# Vision mode - analyze construction site photo
python scripts/call_kimi.py --mode vision --image-url https://example.com/site.jpg --prompt "Assess construction progress"
python scripts/call_kimi.py --mode vision --image-path photos/site_01.jpg --prompt "Check safety compliance"

# Code generation
python scripts/call_kimi.py --mode code --prompt "Generate a Monte Carlo cost forecasting script"

# Document analysis
python scripts/call_kimi.py --mode document --file contracts/main_contract.pdf --prompt "Extract all action items and deadlines"

# Options
python scripts/call_kimi.py --mode chat --prompt "..." --output json    # JSON output
python scripts/call_kimi.py --mode chat --prompt "..." --thinking       # Enable reasoning
python scripts/call_kimi.py --mode chat --prompt "..." --model moonshot-v1-128k  # Override model
```

### MCP Server (mcp-servers/kimi/)

Three tools available when the MCP server is running:

| Tool | Description | Default Model |
|------|-------------|---------------|
| `kimi_vision_analyze` | Analyze images (site photos, drawings, plans) | kimi-k2.5 |
| `kimi_code_generate` | Generate code for construction data analysis | kimi-k2.5 |
| `kimi_document_analyze` | Analyze documents with long-context support | moonshot-v1-128k |

MCP server config is in `.mcp.json` at the project root.

### Environment Variables

Required: `MOONSHOT_API_KEY` in `.env`

Optional overrides:
- `KIMI_MODEL` (default: kimi-k2.5)
- `KIMI_MAX_TOKENS` (default: 4096)
- `KIMI_TEMPERATURE` (default: 0.7)
- `KIMI_BASE_URL` (default: https://api.moonshot.ai/v1)

## Existing AI Patterns (for consistency)

- **OpenAI chat**: `backend/api/chat.py` — RAG-based chat with document citations
- **Vision service**: `backend/services/vision.py` — httpx client pattern with bearer auth and custom exceptions
- **Connector factory**: `backend/connectors/factory.py` — registry of callables with stub fallback
- **Intent routing**: `backend/services/intent_router.py` — regex-based intent classification
- **Settings**: `backend/config.py` — Pydantic BaseSettings with env variable mapping

## Security Notes

- Never commit `.env` files — all secrets via environment variables
- `MOONSHOT_API_KEY`, `OPENAI_API_KEY` must be set via env, not hardcoded
- Production requires `JWT_SECRET_KEY` to be properly set
- Use `USE_STUB_CONNECTORS=true` for development without live external services
