# Start Here: AI Agent Onboarding

**Last Updated**: 2026-01-13
**Project Status**: Early implementation (42 LOC), comprehensive planning complete
**Current Branch**: `claude/analyze-capture-upload-fO8SH`

---

## 30-Second Overview

**What**: Self-hosted personal AI memory layer (capture → enrich → store → retrieve → synthesize)
**Why**: Give AI conversations persistent context without SaaS vendor lock-in
**Who**: Technical users comfortable with Docker Compose
**Stage**: Planning complete, v1 implementation starting
**Tech**: Python 3.11 + FastAPI + PostgreSQL + pgvector + Celery + OpenAI embeddings

---

## What Works Right Now

- ✅ FastAPI server runs (`make api`)
- ✅ Docker infrastructure (PostgreSQL, Redis, Flower) ready
- ✅ Test framework (pytest-bdd) configured
- ✅ `/v1/capture` endpoint exists (returns mock response)
- ❌ **Nothing persists to database yet**
- ❌ **No actual capture/retrieval working**

**Critical**: The capture endpoint doesn't actually save data. It's a stub.

---

## The Down-Scoped V1 Plan

### What We're Building (Minimum Lovable Product)

**Core Flow**:
```
Browser Extension → POST /v1/capture → Save to DB + Embed → Return success
                                                    ↓
Later: Extension → POST /v1/retrieve/semantic → pgvector search → Inject into LLM
```

**Features**:
1. ✅ Capture text via API (synchronous, 2-3 sec response)
2. ✅ Upload file (PDF/DOCX/TXT) → extract text → save
3. ✅ Generate OpenAI embedding on capture
4. ✅ Store in PostgreSQL (`content_items` + `embeddings` tables)
5. ✅ Semantic search via pgvector
6. ✅ Recent items endpoint (simple list)
7. ✅ Dead-simple browser extension (popup with textarea)

**What's Cut (For Now)**:
- ❌ Async Celery queue (v1 is synchronous)
- ❌ Classification, keywords, themes (Stage 2 - defer)
- ❌ Relationship detection (too complex for v1)
- ❌ Command palette UI (simple popup first)
- ❌ Status tracking endpoint (not needed if synchronous)
- ❌ Weekly synthesis (Stage 5 - way later)

### Key Simplification: Synchronous V1

**Original Plan**: Capture → Celery queue → Async enrichment → Storage
**V1 Reality**: Capture → Embed + Save (in request) → Return (2-3 sec)

**Why**: Eliminates Celery complexity, proves value faster, can optimize later.

---

## Architecture Quick Reference

### Five Stages (Only Stage 1 + minimal Stage 3/4 in V1)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Capture   │───▶│ Enrichment  │───▶│   Storage   │───▶│  Retrieval  │───▶│Intelligence │
│  (<100ms)   │    │  (async)    │    │  (persist)  │    │  (<500ms)   │    │  (optional) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
  FastAPI          Celery +           PostgreSQL +        FastAPI            Celery
                   Claude/OpenAI      pgvector
```

**V1 Scope**: Stage 1 (capture) + Stage 3 (storage) + Stage 4 (retrieval) only.

### Database Schema (V1 Tables Only)

**content_items**:
```sql
CREATE TABLE content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) UNIQUE,  -- SHA-256 for deduplication
    source VARCHAR(100) NOT NULL,      -- 'manual_entry', 'file_upload', etc.
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    captured_at TIMESTAMP
);
```

**embeddings**:
```sql
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_item_id UUID REFERENCES content_items(id) ON DELETE CASCADE,
    embedding_vector vector(1536),     -- OpenAI text-embedding-3-small
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON embeddings USING hnsw (embedding_vector vector_cosine_ops);
```

**Note**: Other tables (keywords, themes, relationships, etc.) exist in schema docs but NOT in v1.

---

## Key Files & Locations

### Implementation (Where to Code)

| File | Purpose | Status |
|------|---------|--------|
| `src/capture/api.py` | FastAPI endpoints | 42 lines, stub only |
| `src/storage/models.py` | SQLAlchemy models | **Doesn't exist yet** |
| `src/storage/database.py` | DB connection + session | **Doesn't exist yet** |
| `src/shared/embeddings.py` | OpenAI embedding wrapper | **Doesn't exist yet** |
| `alembic/versions/001_initial.py` | Initial migration | **Doesn't exist yet** |

### Documentation (Read for Context)

**V1 Reference (Read These)**:
| File | What It Covers | Priority |
|------|----------------|----------|
| `docs/architecture/build-decisions.md` | Why PostgreSQL, why Celery, all tech choices | 🔴 Read first |
| `docs/architecture/pdc-principles.md` | Core philosophy, prevents scope creep | 🔴 Read first |
| `docs/v1-reference/api-v1.md` | V1 API spec (4 endpoints only) | 🔴 Essential |
| `docs/v1-reference/schema-v1.md` | V1 database schema (2 tables only) | 🔴 Essential |
| `docs/v1-reference/browser-extension-v1.md` | Simple popup extension (~200 LOC) | 🔴 Essential |

**Future Vision (Ignore Until V1 Ships)**:
| File | What It Covers | When to Read |
|------|----------------|--------------|
| `docs/v2-vision/browser-plugin-full.md` | Command palette + ghost button (1381 lines) | After V1 proves valuable |
| `docs/v2-vision/README.md` | What's deferred and why | When tempted to add features |
| `docs/api/endpoints-overview.md` | Complete API spec (25+ endpoints) | V2+ planning |
| `docs/data-models/schema-overview.md` | Full 9-table schema | V2+ planning |
| `docs/features/roadmap.md` | 25+ features with acceptance criteria | V2+ planning |

### Configuration

| File | Purpose |
|------|---------|
| `.env.example` | All environment variables (195 lines) |
| `pyproject.toml` | Python dependencies |
| `infrastructure/docker-compose.yml` | PostgreSQL, Redis, Flower services |
| `Makefile` | Dev commands (`make api`, `make test`, etc.) |

---

## Development Quick Start

```bash
# 1. Start infrastructure
make services              # PostgreSQL + Redis + Flower

# 2. Create .env from example
cp .env.example .env
# Add your OPENAI_API_KEY for embeddings

# 3. Run migrations (once they exist)
make migrate

# 4. Start API server
make api                   # http://localhost:8000

# 5. Run tests
make test
```

---

## What to Build Next (V1 Implementation Order)

### Phase 1: Database Layer (2-3 hours)

1. **Create storage module structure**:
   ```
   src/storage/
   ├── __init__.py
   ├── database.py       # DB connection, session management
   ├── models.py         # SQLAlchemy models (content_items, embeddings)
   └── repositories.py   # CRUD operations (optional)
   ```

2. **SQLAlchemy models** (`src/storage/models.py`):
   - `ContentItem` model matching `content_items` table
   - `Embedding` model matching `embeddings` table
   - Use SQLAlchemy 2.0 style (declarative)

3. **Alembic migration** (`alembic/versions/001_initial_schema.py`):
   - Create `content_items` table
   - Create `embeddings` table
   - Add pgvector HNSW index
   - Run: `make migrate`

4. **Test database connection**:
   - Create test that inserts + queries content_item
   - Verify pgvector extension loaded

### Phase 2: Embeddings Integration (1-2 hours)

1. **Create embeddings module** (`src/shared/embeddings.py`):
   - Wrapper for OpenAI `text-embedding-3-small`
   - Error handling (API failures, rate limits)
   - Retry logic with exponential backoff
   - Model version tracking

2. **Add configuration**:
   - Read `OPENAI_API_KEY` from env
   - Add timeout settings
   - Add model version constant

3. **Write tests**:
   - Mock OpenAI API call
   - Test error handling
   - Verify 1536-dimensional output

### Phase 3: Capture Endpoint V2 (1-2 hours)

1. **Update `/v1/capture` endpoint** (`src/capture/api.py`):
   - Keep existing Pydantic models
   - Add database session dependency
   - Generate embedding via OpenAI
   - Save `ContentItem` + `Embedding` to DB
   - Return capture_id (real UUID from DB)
   - Handle errors (OpenAI failures, DB errors)

2. **Add deduplication**:
   - Calculate SHA-256 hash of content
   - Check for existing content_hash
   - Return existing capture_id if duplicate

3. **Update tests** (`tests/features/01-capture-basic.feature`):
   - Test actual DB persistence
   - Test duplicate detection
   - Test OpenAI API failure handling

### Phase 4: File Upload Endpoint (2-3 hours)

1. **Create file processing module** (`src/capture/file_processors.py`):
   - `extract_text_from_pdf()` using pypdf
   - `extract_text_from_docx()` using python-docx
   - `extract_text_from_txt()` (simple read)
   - File type detection

2. **Add `/v1/capture/file` endpoint** (`src/capture/api.py`):
   - Accept `multipart/form-data`
   - Validate file size (< 10 MB)
   - Validate file type (PDF/DOCX/TXT)
   - Extract text
   - Reuse capture logic (embed + save)
   - Return capture_id + filename + text preview

3. **Write feature tests** (`tests/features/02-capture-file.feature`):
   - Test PDF upload
   - Test DOCX upload
   - Test file too large
   - Test unsupported file type

### Phase 5: Retrieval Endpoints (2-3 hours)

1. **Semantic search** (`POST /v1/retrieve/semantic`):
   - Accept query text + limit (default 5)
   - Generate query embedding
   - pgvector cosine similarity search
   - Return ranked list of content_items
   - Include similarity scores

2. **Recent items** (`GET /v1/retrieve/recent`):
   - Accept limit (default 20)
   - Simple ORDER BY created_at DESC
   - Return list of content_items

3. **Write feature tests** (`tests/features/03-retrieval.feature`):
   - Seed DB with test data
   - Test semantic search returns relevant items
   - Test recent items ordered correctly

### Phase 6: Browser Extension (4-6 hours)

1. **Manifest + structure**:
   ```
   browser-extension/
   ├── manifest.json         # Chrome Extension Manifest v3
   ├── popup.html           # Simple UI
   ├── popup.js             # Save + retrieve logic
   ├── styles.css           # Minimal styling
   └── icons/               # Extension icons
   ```

2. **Popup UI** (`popup.html`):
   - Textarea for content input
   - "Save" button
   - "Get Context" button (for retrieval)
   - Status messages (success/error)

3. **Save functionality** (`popup.js`):
   - POST to `http://localhost:8000/v1/capture`
   - Handle API response
   - Show success/error message

4. **Retrieve functionality** (`popup.js`):
   - Get current tab URL + title as context
   - POST to `/v1/retrieve/semantic`
   - Format results
   - Copy to clipboard (for pasting into LLM)

5. **Manual testing**:
   - Load unpacked in Chrome
   - Save 10-20 diverse items
   - Test retrieval with different queries
   - Fix bugs

---

## Testing Philosophy

### ATDD with Gherkin (pytest-bdd)

**Pattern**:
1. Write Gherkin feature file (`tests/features/*.feature`)
2. Implement step definitions (`tests/step_defs/test_*.py`)
3. Run tests (they fail)
4. Implement feature
5. Tests pass

**Example** (`tests/features/01-capture-basic.feature`):
```gherkin
Feature: Basic Text Capture
  Scenario: Successfully capture text
    Given the API is running
    When I send a POST request to "/v1/capture" with body:
      """
      {
        "content": "Remember to buy milk",
        "source": "quick_note"
      }
      """
    Then the response status code should be 201
    And the response should contain "capture_id"
    And the content should be persisted in the database
```

**Run**: `make test` or `pytest tests/`

---

## Common Pitfalls & Solutions

### 1. pgvector Extension Not Loaded
**Symptom**: `ERROR: type "vector" does not exist`
**Solution**: Run in PostgreSQL: `CREATE EXTENSION IF NOT EXISTS vector;`
**Note**: Already in `infrastructure/init-db.sql` but may need manual run

### 2. OpenAI API Rate Limits
**Symptom**: `RateLimitError` on many captures
**Solution**: Add exponential backoff + retry (max 3 attempts)
**Note**: Free tier = 3 RPM, paid tier = 3500 RPM

### 3. Large File Text Extraction OOM
**Symptom**: Memory error on large PDFs
**Solution**: Stream processing + chunk large files
**V1 Workaround**: Enforce 10 MB limit strictly

### 4. Duplicate Content Detection
**Symptom**: Same content saved multiple times
**Solution**: SHA-256 hash + UNIQUE constraint on content_hash
**Note**: Already in schema, implement in capture endpoint

### 5. Embedding Dimension Mismatch
**Symptom**: `ERROR: vector dimension mismatch`
**Solution**: Verify OpenAI model = `text-embedding-3-small` (1536 dims)
**Note**: Do NOT use `text-embedding-3-large` (3072 dims) without schema change

---

## Design Principles (From `docs/architecture/pdc-principles.md`)

1. **Data Ownership**: User owns everything, self-hosted only
2. **Solution Agnostic**: Works with any LLM (Claude, GPT, Gemini, etc.)
3. **Minimal Friction**: Capture should be <100ms perceived time
4. **Progressive Enhancement**: Simple first, add intelligence over time
5. **Privacy First**: No telemetry, no cloud dependencies (except LLM APIs)

---

## Performance Targets

| Operation | Target | V1 Reality | Notes |
|-----------|--------|------------|-------|
| Capture | <100ms | 2-3 sec | V1 is synchronous (OpenAI embed) |
| Retrieval | <500ms | ~200ms | pgvector HNSW is fast |
| File upload | <5 sec | ~5 sec | Depends on file size |

**Note**: V1 violates <100ms capture target. Acceptable for MVP. Optimize with async queue in v2.

---

## Environment Variables (Key Ones for V1)

```bash
# Database
DATABASE_URL=postgresql://pdc_user:pdc_password@localhost:5432/pdc

# OpenAI (required for embeddings)
OPENAI_API_KEY=sk-...

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["chrome-extension://*"]  # For browser extension

# Optional
MAX_CONTENT_LENGTH=100000  # 100k chars
MAX_FILE_SIZE_MB=10
```

---

## When You Get Stuck

### 1. Read Existing Docs
- `docs/architecture/build-decisions.md` - **Why** we made tech choices
- `docs/api/endpoints-overview.md` - API contracts
- `docs/data-models/schema-overview.md` - Database schema

### 2. Check Tests
- `tests/features/*.feature` - Acceptance criteria in plain English
- `tests/step_defs/*.py` - How features should behave

### 3. Ask These Questions
- "Is this essential for v1?" (If no, defer it)
- "Can I simplify this?" (Always yes)
- "Does this block the core flow?" (Capture → Store → Retrieve)

### 4. Common Issues
- **Import errors**: Check `pyproject.toml`, run `poetry install`
- **DB connection fails**: Run `make services`, check `.env`
- **Tests fail**: Check test database is running (port 5433)
- **OpenAI errors**: Verify API key in `.env`

---

## Success Criteria for V1

**You can claim v1 is "done" when**:

1. ✅ You can POST text to `/v1/capture` and it saves to DB
2. ✅ You can upload a PDF and it extracts + saves text
3. ✅ You can query `/v1/retrieve/semantic` and get relevant results
4. ✅ Browser extension can save content
5. ✅ Browser extension can retrieve + copy context
6. ✅ All core feature tests pass
7. ✅ You've used it yourself for 3 days and it's useful

**Not required for v1**:
- ❌ Beautiful UI (functional > pretty)
- ❌ Perfect error messages (good enough > perfect)
- ❌ Full test coverage (core flows > 100% coverage)
- ❌ Production deployment (local dev first)

---

## What Comes After V1

**Once v1 works**:
1. Use it yourself for 2 weeks
2. Document what's annoying/broken
3. Decide: Add async queue (Celery) or keep simple?
4. Add one (1) enrichment feature (probably classification)
5. Improve browser extension UX (command palette?)
6. Consider: Is this useful? Should I continue?

**Don't prematurely optimize**. Let real usage guide v2.

---

## For Future AI Agents

**When you (another Claude instance) are spawned to work on this repo**:

1. Read this file first (you are here)
2. Run: `make services && make api` to verify system works
3. Check git status to see what's in progress
4. Ask user: "What should I work on next?"
5. Reference the implementation order above
6. Build incrementally, test frequently
7. Update this file if you learn something important

**Remember**: This is a collaboration between human + AI, a few hours a week. Build small, working increments. Commit often. Document decisions.

---

## Meta Note

This document exists because comprehensive docs + AI agents = rapid development velocity. You're reading proof of the concept. An AI agent explored this repo, built a mental model, and created this guide - all in one session.

**The irony**: We're building a context substrate for AI using a context substrate for AI development.

Welcome to the recursive loop. Let's build this thing.

---

**Last Session**: 2026-01-13 - Down-scoped v1, created this guide, reorganized docs
**Documentation Structure**: V1-focused docs in `v1-reference/`, future vision in `v2-vision/`
**Next Session**: Start Phase 1 (Database Layer) or Phase 2 (Embeddings)
**Current Commit**: On branch `claude/analyze-capture-upload-fO8SH`
