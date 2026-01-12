# Context Substrate - Build Architecture & Decisions

**Project**: Personal Context Collection & Management System
**Document Type**: Architectural Planning & Decisions
**Last Updated**: 2026-01-12
**Status**: Planning Phase

---

## Executive Summary

This document captures the core architectural decisions for building the Context Substrate system—a five-stage infrastructure for capturing, enriching, storing, retrieving, and synthesizing personal context for AI agents.

**Key Principles:**
- Infrastructure mindset: Reliability over novelty
- ATDD methodology: Gherkin acceptance criteria before code
- Capture velocity: <100ms capture response time
- Metadata quality: Value comes from enrichment, not raw storage
- Separation of concerns: Five distinct stages

---

## PDC Core Principles: Data Sovereignty First

This system implements the **Personal Data Collector (PDC)** vision, where data ownership and user sovereignty are non-negotiable.

### 1. You Own Your Data
**All data resides under your control.**
- Self-hosted infrastructure (Docker Compose for local deployment)
- No third-party services required (PostgreSQL, Redis run locally)
- No data sent to external services except your chosen LLM providers
- Export everything at any time (full JSON/CSV dumps)
- Open schema, inspectable database

**Deployment Options:**
- Local machine (laptop, desktop)
- Personal server (home server, NAS)
- Your own VPS (DigitalOcean, Linode, etc.)
- Your own cloud VM (AWS EC2, GCP Compute, etc.)

**You choose. We don't host anything.**

### 2. Solution Agnostic
**Works with any LLM, any workflow, any client.**
- REST APIs (not proprietary SDK)
- Standard formats (JSON, Markdown)
- Browser plugin works with Claude, ChatGPT, Copilot, any LLM interface
- Can integrate with any tool via HTTP API

**This is infrastructure, not a product.** You bring your own LLM. You bring your own hosting. You control everything.

### 3. Minimal Friction Capture
**Capturing knowledge must never interrupt flow.**
- <100ms API response (FastAPI async endpoints)
- One-click browser plugin (no forms, no fields)
- Async enrichment (don't wait for LLM processing)
- Queue-based architecture (capture succeeds even if downstream fails)

**The best capture system is the one you actually use.** If it takes more than 2 seconds, you won't use it consistently.

### 4. Progressive Enhancement
**Start simple. Add complexity as needed.**
- MVP = Capture + Store + Basic Retrieval (3 stages)
- Enrichment is optional (can disable LLM calls)
- Intelligence is optional (can disable weekly summaries)
- Browser plugin is optional (API works standalone)

**Don't require features you don't need.** The system should work at whatever level of sophistication you want.

### How These Principles Influence Technical Decisions

| PDC Principle | Technical Choice | Why |
|---------------|------------------|-----|
| Data Sovereignty | PostgreSQL (not cloud DB) | Database runs on your machine |
| Data Sovereignty | Redis (not AWS SQS) | Queue runs locally |
| Data Sovereignty | Docker Compose | Single-command local deployment |
| Data Sovereignty | Export endpoints | GET /v1/export/all dumps everything |
| Solution Agnostic | REST APIs | Any HTTP client can integrate |
| Solution Agnostic | Dual LLM provider | Not locked to one vendor |
| Solution Agnostic | Standard formats | JSON/Markdown work everywhere |
| Minimal Friction | <100ms capture | FastAPI async, no blocking |
| Minimal Friction | Browser plugin primary | One-click from any page |
| Minimal Friction | Optional metadata | Don't require user input |
| Progressive Enhancement | Feature flags | Turn stages on/off in config |
| Progressive Enhancement | Monorepo structure | Start simple, extract later |

---

## Decision A: Project Structure & Language Choice

### Decision: Python Monorepo (FastAPI + Celery + SQLAlchemy)

**Rationale:**
- Best ML/LLM ecosystem for enrichment tasks
- Mature async support for fast capture (<100ms requirement)
- Single deployment unit simplifies MVP development
- Excellent testing ecosystem (pytest + pytest-bdd)
- Type hints with mypy for infrastructure reliability

**Architecture:**
```
Monorepo with clean module boundaries:
- src/capture/       - FastAPI endpoints, queue interface
- src/enrichment/    - Celery tasks, LLM calls
- src/storage/       - Database models, migrations
- src/retrieval/     - Search, scoring, context packaging
- src/intelligence/  - Synthesis, trend detection
- src/shared/        - Common utilities, config
```

**Tradeoffs Accepted:**
- All stages in one codebase (simpler for MVP, harder to scale independently)
- Python GIL could bottleneck CPU-intensive work (mitigated by Celery workers)

**Future Migration Path:**
- Clean interfaces allow extracting stages to microservices later
- Dependency injection patterns enable service extraction
- Target scale: ≤10k items/day on monorepo, then evaluate extraction

---

## Decision B: Database Architecture

### Decision: PostgreSQL + pgvector + Edge Tables (Single Database)

**Rationale:**
- Simplicity: One database to operate, backup, monitor
- ACID transactions across all data types (relational + vector + graph)
- Lower operational cost and complexity for MVP
- pgvector is production-ready for semantic search
- Graph queries via edge tables and recursive CTEs

**Database Schema Design:**
```sql
-- Relational tables
content_items (id, content, source, created_at, metadata_json)
classifications (item_id, category, confidence)
keywords (item_id, keyword, weight)

-- Vector table (using pgvector extension)
embeddings (item_id, embedding vector(1536), model_version)

-- Graph tables (edge list approach)
relationships (from_item_id, to_item_id, relationship_type, strength)
themes (theme_id, name, description)
theme_memberships (item_id, theme_id, relevance_score)
```

**Performance Benchmarks to Monitor:**
- ✅ Vector search: <500ms for top-20 results on 10k items
- ✅ Graph traversal: <200ms for 2-hop relationship queries
- ✅ Full-text search: <200ms for keyword queries

**Upgrade Triggers:**
If we consistently exceed performance targets above, consider:
1. **Vector upgrade**: Migrate to Pinecone for <50ms semantic search
2. **Graph upgrade**: Migrate to Neo4j for complex graph algorithms

**Future Migration Path:**
- Abstract database access behind repository pattern
- Vector operations isolated in `VectorSearchRepository` interface
- Graph operations isolated in `GraphRepository` interface
- Can swap implementations without changing business logic

**Considered But Rejected:**
- PostgreSQL + Pinecone + Neo4j: Too complex for MVP, high ops burden
- PostgreSQL + Pinecone only: Graph data still needs storage, adds complexity

**Architectural Note:**
> **PLAN TO UPGRADE**: This is an intentional MVP decision. We expect to migrate to specialized databases (Pinecone for vectors, potentially Neo4j for complex graph queries) once we validate the system with real usage patterns and hit performance limits.

---

## Decision C: Message Queue Choice

### Decision: Redis + Celery

**Rationale:**
- Mature Python/Celery integration (battle-tested)
- Dual-purpose: Message queue + cache (single service)
- Fast in-memory operations support <100ms capture
- Excellent monitoring (Flower dashboard)
- Rich task routing, prioritization, retry patterns

**Configuration:**
```python
# Celery setup
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

# Redis persistence (acceptable durability)
# redis.conf: appendonly yes, appendfsync everysec
```

**Dual-Purpose Usage:**
1. **Message Queue**:
   - Capture → Enrichment tasks
   - Storage → Intelligence synthesis jobs

2. **Cache**:
   - LLM response caching (reduce API costs)
   - Rate limiting state
   - Session data

**Monitoring Plan:**
- Flower dashboard for queue depth, task latency
- Custom metrics for failure rates
- Alert if queue depth > 1000 (backlog indicator)

**Tradeoffs Accepted:**
- Redis persistence weaker than RabbitMQ (AOF/RDB tradeoffs)
- Memory-bound (need to size appropriately)
- Acceptable risk: Context collection isn't mission-critical (users can re-submit)

**Upgrade Trigger:**
If message loss becomes unacceptable (e.g., >0.1% loss rate), migrate to RabbitMQ for stronger durability guarantees.

**Considered But Rejected:**
- RabbitMQ: More durable but adds operational overhead (need Redis anyway for caching)
- AWS SQS: Vendor lock-in, local dev complexity, not committed to AWS yet

---

## Decision D: LLM Provider for Enrichment

### Decision: Dual Provider Strategy (Claude + OpenAI)

**Rationale:**
- Best tool for each job: Claude excels at structured extraction, OpenAI has proven embeddings
- Hedge against single provider outages or rate limits
- Cost-effective: Claude Haiku for high-volume tasks, Sonnet for complex analysis
- Flexibility to compare and optimize over time

**Implementation:**
```python
# Enrichment tasks (Anthropic Claude)
ENRICHMENT_TASKS = {
    'classification': 'claude-haiku-3-5-20241022',      # Fast, cheap
    'keyword_extraction': 'claude-haiku-3-5-20241022',  # Fast, cheap
    'theme_detection': 'claude-sonnet-4-5-20250929',    # Better reasoning
    'summarization': 'claude-sonnet-4-5-20250929',      # Quality matters
    'relationship_detection': 'claude-sonnet-4-5-20250929'  # Complex analysis
}

# Embedding generation (OpenAI)
EMBEDDING_MODEL = 'text-embedding-3-small'  # 1536 dimensions
```

**Cost Estimate** (10,000 items/month):
- Claude Haiku (classification + keywords): ~$5-10/month
- Claude Sonnet (themes + summaries + relationships): ~$20-30/month
- OpenAI embeddings: ~$2-5/month
- **Total: ~$30-45/month**

**Tradeoffs Accepted:**
- Two API keys to manage (more configuration)
- Two potential failure modes (need error handling for both)
- Slightly more complex retry logic

**Benefits:**
- Resilience: If one provider has issues, can still capture content
- Optimization: Can A/B test models within each provider
- Future flexibility: Can swap providers for specific tasks

**Considered But Rejected:**
- Claude only: No embeddings API (would need 2 providers anyway)
- OpenAI only: Less reliable structured output, potentially higher cost at scale

---

## Decision E: Testing Framework Strategy (PENDING)

**Status**: To be decided next

**Options under consideration:**
1. pytest + pytest-bdd (Gherkin support in Python)
2. behave (Python Gherkin-native framework)
3. pytest for tests + Gherkin docs separate

---

## System Architecture Overview

### Five-Stage Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │    │             │
│   Capture   │───▶│ Enrichment  │───▶│   Storage   │───▶│  Retrieval  │───▶│Intelligence │
│  (<100ms)   │    │  (async)    │    │  (persist)  │    │  (<500ms)   │    │  (batch)    │
│             │    │             │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                   │                   │                   │                   │
   FastAPI            Celery           PostgreSQL          FastAPI            Celery
   endpoints          workers           +pgvector           endpoints          jobs
```

### Technology Stack Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Framework | FastAPI | Fast capture/retrieval endpoints |
| Task Queue | Celery | Async enrichment processing |
| Message Broker | Redis | Queue + cache dual-purpose |
| Database | PostgreSQL + pgvector | Relational + vector + graph storage |
| LLM Provider | TBD | Metadata extraction & embeddings |
| Testing | pytest + pytest-bdd | ATDD with Gherkin specs |
| Deployment | Docker Compose | Local dev environment |

---

## Development Methodology

### ATDD (Acceptance Test-Driven Development)

**Process for each feature:**
1. Write Gherkin acceptance criteria (`.feature` file)
2. Get user approval on acceptance criteria
3. Write step definitions (Red phase - tests fail)
4. Implement minimal code (Green phase - tests pass)
5. Refactor for quality (Refactor phase - tests stay green)
6. Document and move to next feature

**No code without failing test first.**

---

## Project Structure (Planned)

```
context-substrate/
├── docs/
│   ├── architecture/        # This file + future ADRs
│   ├── api/                 # OpenAPI specs
│   └── diagrams/            # System architecture diagrams
├── tests/
│   ├── features/            # Gherkin .feature files
│   ├── step_defs/           # pytest-bdd step definitions
│   ├── integration/         # Integration test suites
│   └── fixtures/            # Test data and mocks
├── src/
│   ├── capture/             # Stage 1: API, queue interface
│   ├── enrichment/          # Stage 2: Celery tasks, LLM
│   ├── storage/             # Stage 3: Models, migrations
│   ├── retrieval/           # Stage 4: Search, scoring
│   ├── intelligence/        # Stage 5: Synthesis, trends
│   └── shared/              # Common utilities
├── infrastructure/
│   ├── docker-compose.yml   # Local dev environment
│   └── migrations/          # Database schema evolution
├── .env.example
├── pyproject.toml           # Poetry dependencies
└── README.md
```

---

## Next Steps

1. ✅ **Completed**: Language choice (Python monorepo)
2. ✅ **Completed**: Database architecture (PostgreSQL + pgvector)
3. ✅ **Completed**: Message queue (Redis + Celery)
4. ⏳ **Next**: LLM provider selection
5. ⏳ **Next**: Testing framework decision
6. ⏳ **Next**: Generate project scaffold
7. ⏳ **Next**: Begin ATDD implementation (Feature 1.1: Capture endpoint)

---

## Success Criteria

The system is complete when:
- ✅ All 20+ feature acceptance tests pass
- ✅ Performance: Capture <100ms, Retrieval <500ms
- ✅ APIs documented with OpenAPI specs
- ✅ Docker Compose runs all services locally
- ✅ End-to-end integration test (capture → retrieve → agent packaging)
- ✅ README with clear setup instructions

---

## Notes & Observations

*This section will capture design insights, edge cases discovered, and lessons learned during implementation.*

---

**Document Owner**: Claude Code Agent
**Review Cadence**: Updated after each major architectural decision or milestone
