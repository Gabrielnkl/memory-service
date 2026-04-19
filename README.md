# Memory Service API

A production-ready memory service for AI agents built with FastAPI, LangChain, PostgreSQL, Redis, and Chroma vector database.

## Overview

Memory Service provides a unified API for AI agents to:
- **Store** chat history and messages persistently
- **Recall** recent context from cache
- **Search** semantically similar messages using vector embeddings
- **Manage** user memory across multiple conversation sessions

## Architecture

```
┌─────────────┐
│   FastAPI   │  REST API endpoints
└──────┬──────┘
       │
    ┌──┴──┬──────────┬─────────┐
    │     │          │         │
    ▼     ▼          ▼         ▼
┌────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐
│Postgres│  │  Redis   │  │ Chroma │  │LangChain │
│(Long)  │  │(Recent)  │  │(Vector)│  │(Embed)   │
└────────┘  └──────────┘  └────────┘  └──────────┘
```

- **PostgreSQL**: Persistent storage for full chat history
- **Redis**: In-memory cache for recent messages (fast access)
- **Chroma**: Vector database for semantic search
- **LangChain**: Unified interface for embeddings (OpenAI / HuggingFace)

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Server**: Uvicorn
- **Database**: PostgreSQL 15 + asyncpg
- **Cache**: Redis 7
- **Vector DB**: Chroma 1.3+
- **LangChain**: 1.2+ with OpenAI & HuggingFace embeddings
- **Python**: 3.11+

## Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local dev)
- Redis 7+ (for local dev)
- OpenAI API key (optional, falls back to HuggingFace embeddings)

### Option 1: Docker Compose (Recommended)

```bash
# Clone/setup project
cd memory-service

# Build and start all services
docker compose up --build
```

The API will be available at `http://localhost:8000`.

### Option 2: Local Development

#### 1. Set up environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configure environment variables

```bash
# Create .env file
cp .env.example .env
# Edit .env with your settings
```

#### 3. Start services

```bash
# Terminal 1: PostgreSQL (if not running)
# Terminal 2: Redis
redis-server

# Terminal 3: FastAPI app
uvicorn app.main:app --reload
```

API will be at `http://localhost:8000`.

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service status.

### Store Message
```bash
POST /api/store
Content-Type: application/json

{
  "user_id": "user123",
  "text": "Hello, remember this for later",
  "metadata": {"source": "chat"}
}
```

### Recall Memory
```bash
GET /api/recall?user_id=user123&limit=10
```
Returns recent messages from cache and database.

### Search Memory
```bash
POST /api/search
Content-Type: application/json

{
  "user_id": "user123",
  "query": "What did I say about budgets?",
  "limit": 5
}
```
Returns semantically similar messages using vector search.

## Environment Variables

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=memory_user
POSTGRES_PASSWORD=memory_pass
POSTGRES_DB=memory_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_TTL=3600
REDIS_MAX_MESSAGES=10

# LangChain / Embeddings
OPENAI_API_KEY=sk-...  # Optional, uses HuggingFace if not set

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Project Structure

```
memory-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   └── routes.py        # API endpoint definitions
│   ├── services/
│   │   ├── memory_service.py    # Orchestrates all storage layers
│   │   └── embedding_service.py # LangChain text embeddings
│   ├── db/
│   │   ├── postgres.py      # PostgreSQL operations
│   │   ├── redis.py         # Redis cache operations
│   │   └── vector_db.py     # Chroma vector store
│   └── models/
│       └── schemas.py       # Pydantic request/response models
├── Dockerfile               # Container build spec
├── docker-compose.yml       # Multi-service orchestration
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project metadata
├── .env                    # Environment variables
└── README.md               # This file
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Database Migrations

Alembic is not yet configured. For now, tables are created automatically on first connection via `async create_tables()`.

### Adding New Endpoints

1. Create handler in `app/api/routes.py`
2. Define request/response models in `app/models/schemas.py`
3. Use `MemoryService` for data operations

Example:
```python
from fastapi import APIRouter
from app.models.schemas import MessageStoreRequest
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api", tags=["memory"])

@router.post("/store")
async def store_message(req: MessageStoreRequest):
    service = MemoryService()
    await service.store_message(req.user_id, req.text)
    return {"status": "stored"}
```

## Performance Notes

- **Redis** caches recent messages → O(1) access for hot data
- **Chroma** enables semantic search → fast similarity matching
- **PostgreSQL** ensures durability → no data loss on restart
- Connection pooling for concurrent requests
- Async/await throughout for non-blocking I/O

## Common Issues

### Port Already In Use
If Redis port 6379 is taken:
```bash
# Stop existing Redis
sudo systemctl stop redis-server

# Or change docker-compose.yml port mapping
```

### Database Connection Refused
Ensure PostgreSQL is running:
```bash
# Check status
sudo systemctl status postgresql

# Start if needed
sudo systemctl start postgresql
```

### Slow Embedding Generation
Switch to OpenAI embeddings in `.env` for faster, higher-quality embeddings:
```env
OPENAI_API_KEY=sk-...
```

## Learning Goals

This project demonstrates:
- ✅ FastAPI + async request handling
- ✅ LangChain integration for AI workflows
- ✅ Multi-layer storage (cache, database, vector DB)
- ✅ REST API design patterns
- ✅ Docker containerization
- ✅ Service-oriented architecture
- ✅ Pydantic data validation
- ✅ Environment-based configuration

## Future Enhancements

- [ ] Database migrations with Alembic
- [ ] User authentication & authorization
- [ ] Message tagging and categorization
- [ ] Conversation sessions/threads
- [ ] WebSocket support for real-time updates
- [ ] GraphQL API alternative
- [ ] Advanced filtering & aggregations
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Rate limiting & quotas

## License

MIT

## Author

Gabriel Caramori
