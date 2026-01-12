# Context Substrate - Feature Roadmap

**Project**: Personal Context Collection & Management System
**Methodology**: Acceptance Test-Driven Development (ATDD)
**Status**: Planning → Implementation Ready

---

## Feature Implementation Order

Features are organized by the five pipeline stages. Each feature will follow the ATDD cycle:
1. Write Gherkin acceptance criteria
2. Implement step definitions (Red)
3. Write minimal code (Green)
4. Refactor (Clean)

**Legend**: ⏳ Planned | 🚧 In Progress | ✅ Complete | ⚠️ Blocked

---

## Stage 1: Ingestion Layer
*Goal: Accept content via API with <100ms response time*

### Feature 1.1: Basic Text Ingestion ⏳
- **Endpoint**: `POST /v1/ingest`
- **Purpose**: Accept text content and queue for enrichment
- **Acceptance Criteria**: `tests/features/01-ingestion-basic.feature`
- **Key Scenarios**:
  - Successfully capture text with metadata
  - Reject requests with missing required fields
  - Return capture_id within 100ms
  - Queue enrichment task to Redis

### Feature 1.2: File Upload Ingestion ⏳
- **Endpoint**: `POST /v1/ingest/file`
- **Purpose**: Accept PDF, DOCX, TXT files
- **Acceptance Criteria**: `tests/features/02-ingestion-files.feature`
- **Key Scenarios**:
  - Extract text from PDF files
  - Extract text from DOCX files
  - Handle plain text files
  - Reject unsupported file types
  - Validate file size limits (<10MB)

### Feature 1.3: Capture Status Tracking ⏳
- **Endpoint**: `GET /v1/status/:captureId`
- **Purpose**: Check processing status of captured content
- **Acceptance Criteria**: `tests/features/03-status-tracking.feature`
- **Key Scenarios**:
  - Return "queued" status immediately after capture
  - Return "enriching" status during LLM processing
  - Return "completed" status when stored
  - Return "failed" status with error details

### Feature 1.4: Ingestion Error Handling ⏳
- **Purpose**: Graceful degradation and clear error messages
- **Acceptance Criteria**: `tests/features/04-ingestion-errors.feature`
- **Key Scenarios**:
  - Handle malformed JSON gracefully
  - Validate content length (max 100k characters)
  - Rate limiting (100 requests/minute per user)
  - Return appropriate HTTP status codes

---

## Stage 2: Enrichment Layer
*Goal: Extract metadata via LLM processing (async via Celery)*

### Feature 2.1: Content Classification ⏳
- **Task**: `classify_content_task`
- **Purpose**: Categorize content (note, idea, reference, task, meeting_notes, etc.)
- **LLM**: Claude Haiku
- **Acceptance Criteria**: `tests/features/05-classification.feature`
- **Key Scenarios**:
  - Classify personal notes
  - Classify technical documentation
  - Classify meeting transcripts
  - Return confidence scores

### Feature 2.2: Keyword Extraction ⏳
- **Task**: `extract_keywords_task`
- **Purpose**: Identify key terms, entities, topics
- **LLM**: Claude Haiku
- **Acceptance Criteria**: `tests/features/06-keywords.feature`
- **Key Scenarios**:
  - Extract 5-10 weighted keywords
  - Identify named entities (people, projects, technologies)
  - Handle technical terminology
  - Deduplicate similar terms

### Feature 2.3: Theme Detection ⏳
- **Task**: `detect_themes_task`
- **Purpose**: Identify high-level themes and topics
- **LLM**: Claude Sonnet
- **Acceptance Criteria**: `tests/features/07-themes.feature`
- **Key Scenarios**:
  - Detect project themes
  - Identify recurring concepts
  - Link to existing themes or create new ones
  - Score theme relevance

### Feature 2.4: Content Summarization ⏳
- **Task**: `summarize_content_task`
- **Purpose**: Generate concise summaries for long content
- **LLM**: Claude Sonnet
- **Acceptance Criteria**: `tests/features/08-summarization.feature`
- **Key Scenarios**:
  - Summarize content >1000 words
  - Generate 2-3 sentence summary
  - Preserve key facts and context
  - Skip summarization for short content

### Feature 2.5: Embedding Generation ⏳
- **Task**: `generate_embedding_task`
- **Purpose**: Create semantic vector for similarity search
- **LLM**: OpenAI text-embedding-3-small
- **Acceptance Criteria**: `tests/features/09-embeddings.feature`
- **Key Scenarios**:
  - Generate 1536-dimension vector
  - Store with model version metadata
  - Handle text chunking for long content
  - Cache embeddings for duplicate content

### Feature 2.6: Relationship Detection ⏳
- **Task**: `detect_relationships_task`
- **Purpose**: Identify connections to existing content
- **LLM**: Claude Sonnet
- **Acceptance Criteria**: `tests/features/10-relationships.feature`
- **Key Scenarios**:
  - Detect "references" relationships (cites another item)
  - Detect "builds_on" relationships (extends an idea)
  - Detect "contradicts" relationships
  - Score relationship strength (0.0-1.0)

---

## Stage 3: Storage Layer
*Goal: Persist enriched content with metadata in PostgreSQL*

### Feature 3.1: Core Schema Creation ⏳
- **Purpose**: Database tables for content and metadata
- **Acceptance Criteria**: `tests/features/11-schema-setup.feature`
- **Key Scenarios**:
  - Create content_items table
  - Create classifications table
  - Create keywords table
  - Create themes and theme_memberships tables
  - Install pgvector extension

### Feature 3.2: Embeddings Storage ⏳
- **Purpose**: Store semantic vectors for similarity search
- **Acceptance Criteria**: `tests/features/12-vector-storage.feature`
- **Key Scenarios**:
  - Store 1536-dimension vectors
  - Index vectors for fast similarity search
  - Track embedding model version
  - Support embedding updates

### Feature 3.3: Relationship Graph Storage ⏳
- **Purpose**: Store content relationships as edge tables
- **Acceptance Criteria**: `tests/features/13-graph-storage.feature`
- **Key Scenarios**:
  - Create relationships table (edge list)
  - Store relationship type and strength
  - Support bidirectional relationships
  - Prevent duplicate relationships

### Feature 3.4: Write Operations ⏳
- **Purpose**: Insert and update content with ACID guarantees
- **Acceptance Criteria**: `tests/features/14-write-operations.feature`
- **Key Scenarios**:
  - Insert new content item with all metadata
  - Update existing content (preserve history)
  - Transaction rollback on partial failure
  - Idempotent writes (handle retries)

### Feature 3.5: Read Operations ⏳
- **Purpose**: Retrieve content by ID and filters
- **Acceptance Criteria**: `tests/features/15-read-operations.feature`
- **Key Scenarios**:
  - Get content by ID
  - Filter by classification
  - Filter by date range
  - Filter by keyword or theme
  - Pagination for large result sets

### Feature 3.6: Full-Text Search ⏳
- **Purpose**: Keyword-based search using PostgreSQL FTS
- **Acceptance Criteria**: `tests/features/16-fulltext-search.feature`
- **Key Scenarios**:
  - Search content and summaries
  - Rank results by relevance
  - Support phrase queries
  - Highlight matching terms

---

## Stage 4: Retrieval Layer
*Goal: Package context for AI agents with <500ms response time*

### Feature 4.1: Semantic Search ⏳
- **Endpoint**: `POST /v1/retrieve/semantic`
- **Purpose**: Find similar content via vector search
- **Acceptance Criteria**: `tests/features/17-semantic-search.feature`
- **Key Scenarios**:
  - Accept natural language query
  - Generate query embedding
  - Find top-K similar items (K=20)
  - Return results with similarity scores
  - Response time <500ms

### Feature 4.2: Temporal Search ⏳
- **Endpoint**: `GET /v1/retrieve/temporal`
- **Purpose**: Find content by time ranges and recency
- **Acceptance Criteria**: `tests/features/18-temporal-search.feature`
- **Key Scenarios**:
  - Search by date range
  - Get most recent N items
  - Filter by "last week", "last month" shortcuts
  - Combine with classification filters

### Feature 4.3: Context Packaging ⏳
- **Endpoint**: `POST /v1/retrieve/context`
- **Purpose**: Package relevant context for LLM prompts
- **Acceptance Criteria**: `tests/features/19-context-packaging.feature`
- **Key Scenarios**:
  - Accept agent query + context requirements
  - Retrieve diverse, relevant items (semantic + temporal)
  - Format as markdown for LLM consumption
  - Deduplicate similar items
  - Stay within token budget

### Feature 4.4: Relevance Scoring ⏳
- **Purpose**: Multi-factor scoring for result ranking
- **Acceptance Criteria**: `tests/features/20-relevance-scoring.feature`
- **Key Scenarios**:
  - Combine semantic similarity score
  - Factor in recency (decay over time)
  - Boost by theme relevance
  - Boost by relationship strength
  - Normalize final score (0.0-1.0)

### Feature 4.5: Result Formatting ⏳
- **Purpose**: Multiple output formats for different consumers
- **Acceptance Criteria**: `tests/features/21-result-formatting.feature`
- **Key Scenarios**:
  - JSON format (structured data)
  - Markdown format (human-readable)
  - Prompt-ready format (optimized for LLM context)
  - Include metadata, summaries, relationships

---

## Stage 5: Intelligence Layer
*Goal: Synthesize insights from accumulated context*

### Feature 5.1: Weekly Synthesis ⏳
- **Task**: `weekly_synthesis_task`
- **Purpose**: Generate weekly summary of captured content
- **Acceptance Criteria**: `tests/features/22-weekly-synthesis.feature`
- **Key Scenarios**:
  - Aggregate last 7 days of content
  - Identify top themes
  - Highlight key moments
  - Generate narrative summary
  - Store as synthetic content item

### Feature 5.2: Theme Trend Detection ⏳
- **Task**: `detect_theme_trends_task`
- **Purpose**: Track which themes are growing/declining
- **Acceptance Criteria**: `tests/features/23-theme-trends.feature`
- **Key Scenarios**:
  - Calculate theme frequency over time
  - Identify emerging themes (new in last 30 days)
  - Identify declining themes (less frequent)
  - Visualize trend direction

### Feature 5.3: Gap Identification ⏳
- **Task**: `identify_gaps_task`
- **Purpose**: Find neglected projects or areas
- **Acceptance Criteria**: `tests/features/24-gap-identification.feature`
- **Key Scenarios**:
  - Detect projects with no captures in 30+ days
  - Identify themes mentioned then abandoned
  - Suggest areas needing attention
  - Rank gaps by prior importance

### Feature 5.4: Recommendation Engine ⏳
- **Task**: `generate_recommendations_task`
- **Purpose**: Suggest connections and next actions
- **Acceptance Criteria**: `tests/features/25-recommendations.feature`
- **Key Scenarios**:
  - Recommend related content to review
  - Suggest connections between ideas
  - Propose next steps for projects
  - Identify collaboration opportunities

---

## Cross-Cutting Features

### Observability ⏳
- Logging (structured JSON logs)
- Metrics (Prometheus-compatible)
- Tracing (request ID propagation)
- Health check endpoints

### Security ⏳
- API key authentication
- Rate limiting
- Input sanitization
- Secrets management

### Performance ⏳
- Response time monitoring
- LLM response caching
- Database query optimization
- Connection pooling

---

## Milestones

### Milestone 1: MVP Ingestion (Features 1.1-1.4) ⏳
Can capture text content and track status.

### Milestone 2: Full Enrichment (Features 2.1-2.6) ⏳
LLM pipeline extracts all metadata types.

### Milestone 3: Storage Complete (Features 3.1-3.6) ⏳
All data persisted with search capabilities.

### Milestone 4: Retrieval Ready (Features 4.1-4.5) ⏳
Agents can query and package context.

### Milestone 5: Intelligence Active (Features 5.1-5.4) ⏳
System generates insights and recommendations.

---

**Next Action**: Begin Feature 1.1 (Basic Text Ingestion) using ATDD methodology.

**Last Updated**: 2026-01-12
