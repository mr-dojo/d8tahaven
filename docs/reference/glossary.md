# Context Substrate - Glossary

**Purpose**: Define key terminology used throughout the system.

---

## System Concepts

### Context Substrate
The underlying infrastructure for capturing, enriching, storing, retrieving, and synthesizing personal context for AI agents. "Substrate" emphasizes it's foundational infrastructure, not an end-user application.

### Five-Stage Pipeline
The architectural organization of the system:
1. **Capture** - Accept content
2. **Enrichment** - Extract metadata via LLM
3. **Storage** - Persist in database
4. **Retrieval** - Query and package context
5. **Intelligence** - Synthesize insights

### Capture Velocity
The speed at which the system can accept new content. Target: <100ms for capture endpoints.

### Metadata is the Product
Philosophical principle: Raw text is commodity. Value comes from extracted metadata (classifications, keywords, themes, relationships, embeddings).

---

## Data Entities

### Content Item
A single piece of captured information (note, idea, document, meeting transcript, etc.). The core entity in the system.

### Capture
The act of adding content to the system. Results in a `capture_id` for tracking processing status.

### Capture ID
Unique identifier (UUID) assigned when content enters the capture stage. Used to track async processing status.

### Item ID
Unique identifier (UUID) for a stored content item in the database. Assigned after enrichment completes.

### Classification
High-level categorization of content type. Examples: `note`, `idea`, `reference`, `task`, `meeting_notes`, `documentation`.

### Keyword
Extracted term or entity from content. Weighted by importance (0.0-1.0). Types: `entity`, `concept`, `technology`, `person`, `project`.

### Theme
High-level topic or subject area that spans multiple content items. Examples: "AI", "Software Architecture", "Phoenix Project".

### Relationship
Directed connection between two content items. Types:
- `references` - Cites or mentions another item
- `builds_on` - Extends or elaborates an idea
- `contradicts` - Disagrees with another item
- `implements` - Puts an idea into practice

### Embedding
Semantic vector representation of content (1536 dimensions for OpenAI text-embedding-3-small). Used for similarity search.

### Similarity Score
Cosine similarity between embeddings (0.0-1.0). Higher = more semantically similar.

### Relevance Score
Multi-factor score combining similarity, recency, theme relevance, and relationship strength (0.0-1.0).

---

## Technical Terms

### ATDD (Acceptance Test-Driven Development)
Development methodology where Gherkin acceptance criteria are written before implementation code. Red-Green-Refactor cycle.

### Gherkin
Human-readable language for writing acceptance criteria. Uses `Feature`, `Scenario`, `Given`, `When`, `Then` keywords.

### Step Definition
Python code that implements a Gherkin step (e.g., `Given the capture service is running`). Bridges acceptance criteria to test code.

### pgvector
PostgreSQL extension for vector similarity search. Supports approximate nearest neighbor search via HNSW or IVFFlat indexes.

### Vector Search
Finding items with similar semantic meaning using embedding similarity (cosine distance).

### Full-Text Search (FTS)
Keyword-based search using PostgreSQL's text search capabilities (`tsvector`, `tsquery`).

### Graph Traversal
Following relationship edges to find connected content items. Example: "Find all items that build on this idea."

### Celery
Python distributed task queue for async processing. Used for enrichment tasks.

### Redis
In-memory data store used for message queue (Celery broker) and caching.

### FastAPI
Modern Python web framework for building APIs. Used for capture and retrieval endpoints.

---

## Enrichment Terms

### LLM (Large Language Model)
AI model used for metadata extraction. Claude (Haiku/Sonnet) for classification/themes, OpenAI for embeddings.

### Enrichment Task
Async Celery job that extracts metadata from content. Six core tasks:
1. Classification
2. Keyword extraction
3. Theme detection
4. Summarization
5. Embedding generation
6. Relationship detection

### Confidence Score
LLM-reported certainty about a classification or extraction (0.0-1.0).

### Chunking
Splitting long content into smaller pieces for embedding generation. Not yet implemented (future feature).

---

## Retrieval Terms

### Semantic Search
Query using natural language. System generates query embedding and finds similar items.

### Temporal Search
Query by time ranges (e.g., "last week", "January 2024").

### Context Packaging
Retrieving and formatting relevant items for inclusion in an LLM agent's prompt. Optimizes for diversity, relevance, and token budget.

### Token Budget
Maximum number of tokens (words/pieces) allowed in packaged context. Typical: 4000-8000 tokens.

### Deduplication
Removing near-duplicate or highly similar items from retrieval results.

### Recency Weight
Parameter (0.0-1.0) controlling how much to favor recent items in relevance scoring.

---

## Intelligence Terms

### Synthesis
Aggregating multiple content items to generate higher-level insights (e.g., weekly summary).

### Weekly Summary
System-generated narrative summarizing captured content over 7 days. Highlights themes and key moments.

### Theme Trend
Tracking frequency of theme mentions over time. Identifies emerging/declining topics.

### Gap Identification
Finding projects or themes with no recent activity. Suggests areas needing attention.

### Recommendation
System-generated suggestion based on content analysis. Types: connections, next actions, collaboration opportunities.

### Synthetic Content
System-generated items (summaries, trends, recommendations) stored alongside user-captured content.

---

## Performance Terms

### P50 / P95 / P99
Percentile metrics. P95 = 95% of requests complete within this time. Used for performance targets.

### Capture Latency
Time from API request to returning `capture_id`. Target: <100ms.

### Enrichment Latency
Time to complete all six enrichment tasks. Target: <30 seconds.

### Retrieval Latency
Time to return search results. Target: <500ms.

### Queue Depth
Number of tasks waiting in Redis queue. Indicator of system load.

---

## Architectural Terms

### Monorepo
Single codebase containing all stages. Opposed to microservices (multiple services/repos).

### Repository Pattern
Design pattern isolating database access behind interfaces. Enables swapping database implementations.

### Dependency Injection
Passing dependencies (database, queue) to components rather than hardcoding. Improves testability.

### Migration Path
Plan for upgrading infrastructure (e.g., PostgreSQL → Pinecone for vectors).

### ADR (Architecture Decision Record)
Document capturing a significant architectural choice, its context, and rationale.

---

## Operational Terms

### Docker Compose
Tool for defining multi-container local development environment (PostgreSQL, Redis, API, workers).

### Alembic
Database migration tool for SQLAlchemy. Manages schema evolution.

### Flower
Web-based monitoring tool for Celery task queue.

### Health Check
Endpoint (`/v1/manage/health`) reporting system component status.

### Observability
System's ability to be monitored (logs, metrics, traces).

---

## Acronyms

- **ACID**: Atomicity, Consistency, Isolation, Durability (database transaction properties)
- **ATDD**: Acceptance Test-Driven Development
- **BDD**: Behavior-Driven Development
- **CRUD**: Create, Read, Update, Delete
- **FTS**: Full-Text Search
- **HNSW**: Hierarchical Navigable Small World (vector index algorithm)
- **LLM**: Large Language Model
- **MVP**: Minimum Viable Product
- **UUID**: Universally Unique Identifier

---

**Usage**: Reference this glossary when encountering unfamiliar terms in documentation or code.

**Last Updated**: 2026-01-12
