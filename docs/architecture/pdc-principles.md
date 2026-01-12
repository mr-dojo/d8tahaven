# PDC Principles - Vision to Technical Implementation

**Document Purpose**: Maps the Personal Data Collector (PDC) vision to Context Substrate technical architecture.

**Last Updated**: 2026-01-12

---

## The PDC Vision

**One sentence**: A personal context layer that captures what you learn and retrieves it into any AI conversation.

**Core value**: Your knowledge compounds. Your AI interactions get better over time. You own everything.

**Core UX**: Save with one click. Get context with one click. Everything else is invisible.

---

## The Problem We're Solving

### User Pain Points
- Knowledge scattered across platforms, tools, and silos
- AI conversations start from zero context every time
- Re-explaining context repeatedly wastes time and cognitive energy
- Accumulated learning doesn't compound into better AI outputs
- No way to inject personal expertise into LLM interactions

### Technical Translation
- **Need**: Fast, frictionless capture (<100ms response)
- **Need**: Semantic retrieval that finds relevant context (not just keywords)
- **Need**: Self-hosted infrastructure (data ownership)
- **Need**: LLM-ready output format (inject directly into prompts)
- **Need**: Automatic enrichment (don't burden user with tagging)

---

## The PDC Core Loop → Technical Architecture

### PDC Stage 1: CAPTURE
**User Experience**: Highlight text → One click → Saved

**Technical Implementation**:
- **Component**: Capture API (FastAPI endpoints)
- **Target**: <100ms response time (return capture_id immediately)
- **Interfaces**:
  - Browser plugin (primary): POST from extension
  - Web dashboard: Manual entry form
  - Mobile app (future): Native capture
  - CLI (future): `pdc save "content"`
- **Queue**: Push to Redis for async enrichment
- **Storage**: Minimal initial record (raw content + timestamp + source)

**Key Files**:
- `src/capture/api.py` - FastAPI endpoints
- `src/capture/validators.py` - Input validation
- `src/capture/queue.py` - Redis queue interface

---

### PDC Stage 2: ENRICH
**User Experience**: Invisible background processing

**Technical Implementation**:
- **Component**: Enrichment Agent (Celery workers)
- **Tasks** (6 async jobs):
  1. Classification (content type: article, idea, note, etc.)
  2. Keyword extraction (entities, concepts, technologies)
  3. Theme detection (high-level topics spanning items)
  4. Summarization (for long content)
  5. Embedding generation (1536-dim vector for semantic search)
  6. Relationship detection (references to other items)
- **LLM Strategy**:
  - Claude Haiku: Fast tasks (classification, keywords)
  - Claude Sonnet: Complex reasoning (themes, relationships)
  - OpenAI: Embeddings (text-embedding-3-small)
- **Resilience**: Retries, fallbacks, graceful degradation

**Key Files**:
- `src/enrichment/tasks.py` - Celery task definitions
- `src/enrichment/llm_client.py` - Claude/OpenAI integrations
- `src/enrichment/extractors.py` - Metadata extraction logic

---

### PDC Stage 3: STORE
**User Experience**: Data sovereignty (you own it, you control it)

**Technical Implementation**:
- **Component**: Storage Layer (PostgreSQL + pgvector)
- **Data Models**:
  - `content_items` - Core table (content, metadata, timestamps)
  - `embeddings` - Vector table (semantic search)
  - `keywords` - Extracted terms with weights
  - `relationships` - Graph edges (item-to-item connections)
  - `themes` - High-level topics
- **Principles**:
  - Append-only (preserve history, no edits)
  - Self-hosted (Docker Compose for local deployment)
  - Export-friendly (JSON, CSV dumps available)
  - Open schema (documented, inspectable)

**Key Files**:
- `src/storage/models.py` - SQLAlchemy models
- `src/storage/repositories.py` - Data access layer
- `infrastructure/migrations/` - Alembic schema versions

---

### PDC Stage 4: RETRIEVE
**User Experience**: Get relevant context with one click

**Technical Implementation**:
- **Component**: Retrieval API (FastAPI endpoints)
- **Search Methods**:
  1. **Semantic search** - Vector similarity (pgvector cosine)
  2. **Temporal search** - Time-range queries
  3. **Keyword search** - Full-text search (PostgreSQL FTS)
  4. **Graph traversal** - Follow relationships
- **Context Packaging**:
  - Takes user query + LLM token budget
  - Returns formatted context block ready to inject
  - Optimizes for diversity (not just top N similar items)
  - Deduplicates near-matches
  - Formats as markdown or JSON
- **Target**: <500ms response time

**Key Files**:
- `src/retrieval/api.py` - FastAPI endpoints
- `src/retrieval/search.py` - Search algorithms
- `src/retrieval/scoring.py` - Relevance scoring
- `src/retrieval/packaging.py` - Context formatting

---

### PDC Stage 5: INTELLIGENCE (Progressive Enhancement)
**User Experience**: Invisible insights (weekly summaries, gap detection)

**Technical Implementation**:
- **Component**: Intelligence Agent (Scheduled Celery jobs)
- **Features** (optional, can be disabled):
  - Weekly synthesis (narrative summary of captured content)
  - Theme trends (emerging/declining topics)
  - Gap identification (neglected projects)
  - Recommendations (connections to explore)
- **Principle**: This is enhancement, not core loop
- **User control**: Can disable, adjust frequency

**Key Files**:
- `src/intelligence/synthesis.py` - Summary generation
- `src/intelligence/trends.py` - Trend detection
- `src/intelligence/scheduler.py` - Cron-like scheduling

---

## PDC Principles → Technical Decisions

### Principle 1: You Own Your Data
**Implication**: Self-hosted infrastructure, no third-party dependencies

**Technical Choices**:
- ✅ Docker Compose for single-command local deployment
- ✅ PostgreSQL (not cloud DB) - runs on your machine/server
- ✅ Redis (not AWS SQS) - local message queue
- ✅ Export endpoints (`GET /v1/export/all`) - full data dump
- ✅ Open source license (to be determined)
- ✅ Clear data schema documentation

**Migration Path**: Can deploy to personal VPS, home server, or cloud VM (your choice)

---

### Principle 2: Solution Agnostic
**Implication**: Works with any LLM, any hosting, any workflow

**Technical Choices**:
- ✅ REST APIs (not proprietary SDK) - any client can integrate
- ✅ Standard formats (JSON, Markdown) - LLM-agnostic output
- ✅ Dual LLM provider (Claude + OpenAI) - not locked to one vendor
- ✅ Browser plugin uses web standards - works with any LLM UI
- ✅ Pluggable storage backend (repository pattern) - can swap DB

**What this enables**: Use with Claude, ChatGPT, Copilot, local LLMs, future tools

---

### Principle 3: Minimal Friction Capture
**Implication**: Capturing must be near-instant, never interrupt flow

**Technical Choices**:
- ✅ <100ms capture response (FastAPI async endpoints)
- ✅ Async enrichment (don't block on LLM calls)
- ✅ Queue-based architecture (capture succeeds even if enrichment delayed)
- ✅ Browser plugin one-click SAVE (no forms, no fields)
- ✅ Keyboard shortcuts (future: `Cmd+Shift+S`)
- ✅ Optional metadata (don't require user input)

**Performance Targets**:
- Capture endpoint: P95 < 100ms
- Queue push: < 10ms
- Return capture_id: immediate

---

### Principle 4: Useful Retrieval
**Implication**: Context must improve LLM interactions (quality over quantity)

**Technical Choices**:
- ✅ Semantic search (vector embeddings) - not just keyword matching
- ✅ Multi-factor relevance scoring (similarity + recency + relationships)
- ✅ Diversity optimization (don't return 10 near-duplicates)
- ✅ Token budget awareness (respect LLM context limits)
- ✅ Context packaging (formatted for direct prompt injection)

**Retrieval Quality Metrics**:
- Latency: P95 < 500ms
- Relevance: User feedback loop (thumbs up/down on retrieved context)
- Diversity: Enforce minimum similarity threshold between results

---

### Principle 5: Append-Only Mindset
**Implication**: Don't edit entries, add new ones. Preserve the journey.

**Technical Choices**:
- ✅ No UPDATE operations on content_items.content field
- ✅ Timestamps preserved (created_at never changes)
- ✅ Versioning for enrichment metadata (track changes over time)
- ✅ Soft deletes (archive flag, not hard delete)
- ✅ Audit log (future: track all operations)

**Database Schema**:
```sql
content_items (
  id UUID PRIMARY KEY,
  content TEXT NOT NULL,              -- Immutable
  created_at TIMESTAMP NOT NULL,      -- Immutable
  enriched_at TIMESTAMP,              -- Last enrichment run
  archived_at TIMESTAMP,              -- Soft delete
  enrichment_version INT DEFAULT 1    -- Track metadata updates
)
```

---

### Principle 6: Progressive Enhancement
**Implication**: Start simple, add complexity as needed. Don't require all features.

**Technical Choices**:
- ✅ MVP = Capture + Store + Basic Retrieval (3 stages minimum)
- ✅ Enrichment is optional (can disable LLM calls, fall back to keywords only)
- ✅ Intelligence stage is optional (can disable weekly summaries)
- ✅ Browser plugin is optional (API works standalone)
- ✅ Configuration-driven feature flags

**Implementation Strategy**:
```python
# config.py
FEATURES = {
    'capture': True,           # Core (always on)
    'enrichment': True,        # Core (always on)
    'storage': True,           # Core (always on)
    'retrieval': True,         # Core (always on)
    'intelligence': False,     # Progressive enhancement (off by default)
    'browser_plugin': True,    # Optional interface
}
```

---

## Primary Interface: Browser Plugin

### SAVE Mode
**User Flow**:
1. User highlights text on any webpage
2. Browser extension detects highlight, shows "Save to PDC" button
3. User clicks → Instantly saved (no forms, no interruption)
4. Visual confirmation (toast notification)
5. Background: Enrichment runs asynchronously

**Technical Implementation**:
- Chrome/Firefox extension manifest v3
- Content script detects text selection
- One-click → POST to capture API
- Extension stores API key (user configures once)
- Captures: content + source URL + timestamp + page title

**API Call**:
```http
POST /v1/capture
Content-Type: application/json
Authorization: Bearer <user_api_key>

{
  "content": "highlighted text here",
  "source": "browser",
  "metadata": {
    "url": "https://example.com/article",
    "title": "Article Title",
    "domain": "example.com"
  }
}

Response:
{
  "capture_id": "uuid-here",
  "status": "captured",
  "message": "Content saved. Enrichment in progress."
}
```

---

### GET Context Mode
**User Flow**:
1. User is in any LLM interface (Claude, ChatGPT, etc.)
2. Types initial prompt: "Help me write about data sovereignty"
3. Clicks "Get Context" button in extension
4. Extension queries PDC retrieval API with prompt text
5. Relevant context block inserted into text field
6. User reviews, edits if needed, sends to LLM

**Technical Implementation**:
- Extension detects common LLM UI text inputs
- "Get Context" button injected near input field
- Click → POST to retrieval API with prompt text
- API returns formatted context block (markdown)
- Extension inserts at cursor position

**API Call**:
```http
POST /v1/retrieve/context
Content-Type: application/json
Authorization: Bearer <user_api_key>

{
  "query": "Help me write about data sovereignty",
  "max_tokens": 4000,
  "format": "markdown"
}

Response:
{
  "context": "## Relevant Context from Your PDC\n\n...",
  "items_count": 5,
  "token_estimate": 1200
}
```

---

## What PDC Is NOT

### Not a Note-Taking App
- ❌ No rich text editor
- ❌ No folder hierarchies
- ❌ No manual organization required
- ✅ Capture layer that works WITH your existing note tools

### Not a Second Brain System
- ❌ No forced tagging or categorization
- ❌ No complex linking workflows
- ❌ No manual curation required
- ✅ Automatic enrichment handles metadata

### Not an AI Product
- ❌ No built-in LLM interface
- ❌ No chat UI
- ❌ No question-answering system
- ✅ Context injection layer for YOUR chosen LLMs

### Not a Cloud Service
- ❌ No SaaS subscription
- ❌ No data sent to our servers
- ❌ No third-party hosting
- ✅ Self-hosted infrastructure you control

---

## Success Metrics

### Technical Metrics
- ✅ Capture latency: P95 < 100ms
- ✅ Enrichment latency: P95 < 30 seconds
- ✅ Retrieval latency: P95 < 500ms
- ✅ System uptime: >99% (local deployment)

### User Experience Metrics
- ✅ Capture friction: <2 clicks from highlight to save
- ✅ Retrieval relevance: User rates context helpful >80% of time
- ✅ LLM output quality: Measurable improvement with PDC context vs. without

### System Health Metrics
- ✅ Queue depth: <1000 items (no backlog)
- ✅ Enrichment success rate: >95%
- ✅ Database size growth: Predictable, scalable

---

## Summary: Vision → Implementation

| PDC Principle | Technical Choice | Rationale |
|---------------|------------------|-----------|
| You own your data | Self-hosted PostgreSQL + Docker Compose | No third-party dependencies |
| Solution agnostic | REST APIs, standard formats, multi-LLM | Works with any LLM or client |
| Minimal friction | <100ms capture, async enrichment | Never interrupt flow |
| Useful retrieval | Semantic search + relevance scoring | Quality over quantity |
| Append-only | Immutable content, soft deletes | Preserve history |
| Progressive enhancement | Feature flags, optional stages | Start simple, grow as needed |

---

**This document is the bridge between user vision (PDC spec) and engineering reality (Context Substrate system).**

**Use this as reference when making technical decisions: Does it align with PDC principles?**

---

**Last Updated**: 2026-01-12
**Document Owner**: Context Substrate Team
