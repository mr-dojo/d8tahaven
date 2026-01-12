# Personal Data Collector (PDC)

**Context Substrate** - A self-hosted infrastructure for capturing, enriching, storing, retrieving, and synthesizing personal context for AI agents.

---

## What is this?

PDC is a **personal context layer** that:
1. **Captures** what you read, think, and learn (browser plugin, API)
2. **Enriches** content automatically with metadata (LLM-powered classification, keywords, themes)
3. **Stores** everything in your own database (PostgreSQL + pgvector)
4. **Retrieves** relevant context for AI conversations (semantic search, context packaging)

**Core Value**: Your knowledge compounds. Your AI interactions get better over time. You own everything.

---

## Core Principles

- **You Own Your Data**: Self-hosted, no third-party services, full control
- **Solution Agnostic**: Works with any LLM (Claude, ChatGPT, Copilot, local models)
- **Minimal Friction**: <100ms capture, one-click browser plugin, no forms
- **Progressive Enhancement**: Start simple (3 stages), add features as needed

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (for PostgreSQL + Redis)
- **Poetry** (Python dependency management)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/context-substrate.git
cd context-substrate

# 2. Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# 3. Install Python dependencies
poetry install

# 4. Start infrastructure services (PostgreSQL + Redis)
docker-compose -f infrastructure/docker-compose.yml up -d

# 5. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY)

# 6. Run database migrations
poetry run alembic upgrade head

# 7. Start the API server
poetry run uvicorn src.capture.api:app --reload

# 8. Start Celery workers (in a separate terminal)
poetry run celery -A src.enrichment.tasks worker --loglevel=info

# 9. (Optional) Start Flower monitoring dashboard
# Open http://localhost:5555 in your browser
```

### Verify Installation

```bash
# Check API health
curl http://localhost:8000/v1/manage/health

# Expected response:
# {"status": "healthy", "database": "connected", "redis": "connected"}
```

---

## Project Structure

```
context-substrate/
├── docs/                       # Complete documentation
│   ├── architecture/           # Build decisions, PDC principles, ADRs
│   ├── features/               # Roadmap with 25+ features
│   ├── api/                    # API endpoint specs
│   ├── data-models/            # Database schema
│   ├── interfaces/             # Browser plugin spec
│   └── reference/              # Glossary
├── src/                        # Source code
│   ├── capture/                # Stage 1: API endpoints, queue
│   ├── enrichment/             # Stage 2: Celery tasks, LLM calls
│   ├── storage/                # Stage 3: Database models
│   ├── retrieval/              # Stage 4: Search, context packaging
│   ├── intelligence/           # Stage 5: Synthesis, trends (optional)
│   └── shared/                 # Common utilities, config
├── tests/                      # Test suite
│   ├── features/               # Gherkin .feature files (ATDD)
│   ├── step_defs/              # pytest-bdd step definitions
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data
├── infrastructure/             # Deployment
│   ├── docker-compose.yml      # Local dev environment
│   └── migrations/             # Database schema evolution
├── pyproject.toml              # Python dependencies
└── README.md                   # This file
```

---

## Usage

### API Endpoints

#### Capture Text Content

```bash
curl -X POST http://localhost:8000/v1/capture \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "content": "This is my note about AI agents and context collection",
    "source": "manual_entry",
    "metadata": {
      "project": "PDC",
      "tags": ["ai", "agents"]
    }
  }'

# Response:
# {
#   "capture_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "queued",
#   "queued_at": "2024-01-15T14:30:01.234Z"
# }
```

#### Check Processing Status

```bash
curl http://localhost:8000/v1/status/{capture_id} \
  -H "X-API-Key: your-api-key"

# Response:
# {
#   "capture_id": "...",
#   "status": "completed",  # or "queued", "enriching", "failed"
#   "enrichment_progress": {
#     "classification": "completed",
#     "keywords": "completed",
#     "embeddings": "completed"
#   }
# }
```

#### Retrieve Context for LLM Prompt

```bash
curl -X POST http://localhost:8000/v1/retrieve/context \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "Help me write about data sovereignty",
    "max_tokens": 4000,
    "format": "markdown"
  }'

# Response:
# {
#   "context": "# Relevant Context\n\n## Note from 2024-01-10\n...",
#   "items_count": 5,
#   "token_estimate": 1200
# }
```

### Browser Plugin (Coming Soon)

The browser plugin provides two modes:

1. **SAVE Mode**: Highlight text on any webpage → Click "Save to PDC" → Instantly captured
2. **GET Context Mode**: In any LLM interface → Click "Get Context" → Relevant items injected into prompt

See `docs/interfaces/browser-plugin-spec.md` for full specification.

---

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run only acceptance tests (ATDD)
poetry run pytest tests/features/

# Run with coverage
poetry run pytest --cov=src

# Run specific feature
poetry run pytest tests/features/01-capture-basic.feature

# Run integration tests only
poetry run pytest -m integration
```

### Code Quality

```bash
# Format code with Ruff
poetry run ruff format .

# Lint code
poetry run ruff check .

# Type check with MyPy
poetry run mypy src/

# Run all quality checks
make lint
```

### Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Add new table"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history
```

### Common Tasks (Makefile)

```bash
make install      # Install dependencies
make dev          # Start dev environment
make test         # Run all tests
make lint         # Run code quality checks
make format       # Format code
make migrate      # Run database migrations
make clean        # Clean up temp files
```

---

## Architecture

### Five-Stage Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Capture   │───▶│ Enrichment  │───▶│   Storage   │───▶│  Retrieval  │───▶│Intelligence │
│  (<100ms)   │    │  (async)    │    │  (persist)  │    │  (<500ms)   │    │  (optional) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     FastAPI           Celery          PostgreSQL           FastAPI            Celery
                                       + pgvector
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Framework | FastAPI | Capture & retrieval endpoints |
| Task Queue | Celery | Async enrichment processing |
| Message Broker | Redis | Queue + cache |
| Database | PostgreSQL + pgvector | Relational + vector + graph |
| LLM (Enrichment) | Claude Haiku/Sonnet | Classification, keywords, themes |
| LLM (Embeddings) | OpenAI text-embedding-3-small | Semantic vectors |
| Testing | pytest + pytest-bdd | ATDD with Gherkin |
| Deployment | Docker Compose | Self-hosted local environment |

---

## Configuration

All configuration is managed via environment variables (`.env` file):

- **API Keys**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- **Database**: `DATABASE_URL` (default: local PostgreSQL)
- **Redis**: `REDIS_URL` (default: local Redis)
- **Feature Flags**: Enable/disable enrichment, intelligence stages
- **Performance Tuning**: Worker concurrency, rate limits, timeouts

See `.env.example` for full configuration options.

---

## Documentation

Comprehensive documentation is in the `docs/` folder:

- **`docs/README.md`**: Documentation navigation
- **`docs/architecture/build-decisions.md`**: All architectural decisions and rationale
- **`docs/architecture/pdc-principles.md`**: PDC vision → technical implementation mapping
- **`docs/features/roadmap.md`**: All 25+ features with acceptance criteria
- **`docs/api/endpoints-overview.md`**: Complete API reference
- **`docs/data-models/schema-overview.md`**: Database schema (9 tables)
- **`docs/interfaces/browser-plugin-spec.md`**: Browser extension specification
- **`docs/reference/glossary.md`**: System terminology

---

## Deployment

### Local (Default)

Docker Compose runs all services on your local machine:

```bash
docker-compose -f infrastructure/docker-compose.yml up -d
poetry run uvicorn src.capture.api:app
poetry run celery -A src.enrichment.tasks worker
```

### Personal Server

Deploy to your own server (home server, NAS, Raspberry Pi):

1. Install Docker + Docker Compose
2. Clone repository
3. Run `docker-compose up -d`
4. Expose port 8000 (optional: use nginx reverse proxy)

### VPS / Cloud VM

Deploy to DigitalOcean, Linode, AWS EC2, etc.:

1. Provision VM (2GB+ RAM recommended)
2. Install Docker + Docker Compose
3. Clone repository
4. Configure firewall (allow port 8000, or use reverse proxy)
5. Run `docker-compose up -d`

**You choose your infrastructure. We don't host anything.**

---

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Capture API latency (P95) | <100ms | TBD |
| Enrichment latency | <30s | TBD |
| Retrieval API latency (P95) | <500ms | TBD |
| Vector search (10k items) | <200ms | TBD |

---

## Roadmap

### MVP (Stages 1-4) - Core PDC Loop

- ✅ Documentation & architecture planning complete
- ⏳ Stage 1: Capture (6 features including browser plugin)
- ⏳ Stage 2: Enrichment (6 LLM-powered tasks)
- ⏳ Stage 3: Storage (6 database features)
- ⏳ Stage 4: Retrieval (5 search & context packaging features)

### Progressive Enhancement (Stage 5) - Optional

- ⏳ Weekly synthesis
- ⏳ Theme trend detection
- ⏳ Gap identification
- ⏳ Recommendation engine

See `docs/features/roadmap.md` for complete feature list.

---

## Contributing

This project is built using **Acceptance Test-Driven Development (ATDD)**:

1. Write Gherkin acceptance criteria (`.feature` file)
2. Implement step definitions (pytest-bdd)
3. Write production code to make tests pass
4. Refactor while keeping tests green

See `docs/architecture/build-decisions.md` for development methodology.

---

## License

MIT License - See LICENSE file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/context-substrate/issues)
- **Documentation**: `docs/` folder
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/context-substrate/discussions)

---

## What Makes PDC Different?

| PDC | Traditional Note Apps | SaaS AI Tools |
|-----|----------------------|--------------|
| You own your data | You own your data | They own your data |
| Self-hosted | Self-hosted or cloud | Cloud only |
| Works with any LLM | N/A | Locked to one LLM |
| Infrastructure (API-first) | Application (UI-first) | Application (UI-first) |
| Automatic enrichment | Manual tagging | Limited automation |
| Semantic search | Keyword search | Often semantic |
| One-click browser capture | Copy-paste workflow | Copy-paste workflow |

---

**Built with the PDC philosophy: Data ownership, solution agnostic, minimal friction, progressive enhancement.**

---

## Next Steps

1. ✅ Read this README
2. ⏳ Install dependencies (`poetry install`)
3. ⏳ Start services (`docker-compose up -d`)
4. ⏳ Configure API keys (`.env` file)
5. ⏳ Run first capture (`curl` or browser plugin)
6. ⏳ Retrieve context for an LLM conversation
7. ⏳ See your knowledge compound over time

**Your AI interactions will never be the same.**
