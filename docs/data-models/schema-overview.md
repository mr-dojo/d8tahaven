# Database Schema Overview

**Database**: PostgreSQL 15+ with pgvector extension
**Purpose**: Unified storage for relational, vector, and graph data

---

## Design Philosophy

1. **Single Source of Truth**: All data in PostgreSQL (no multi-DB sync complexity)
2. **ACID Guarantees**: Transactional consistency across all data types
3. **Denormalization for Performance**: Accept some redundancy for query speed
4. **Metadata-Rich**: Every table includes created_at, updated_at, metadata JSONB

---

## Core Tables

### content_items
**Purpose**: Primary table for all captured content

```sql
CREATE TABLE content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,  -- SHA-256 for deduplication
    source VARCHAR(100) NOT NULL,       -- 'manual_entry', 'file_upload', 'api', etc.

    -- Enrichment results
    classification VARCHAR(50),          -- 'note', 'idea', 'reference', 'task', etc.
    classification_confidence FLOAT,     -- 0.0-1.0
    summary TEXT,                        -- Generated for long content

    -- Metadata
    metadata JSONB DEFAULT '{}',         -- User-provided or extracted metadata

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- When user created it

    -- Status tracking
    processing_status VARCHAR(20) DEFAULT 'queued',  -- 'queued', 'enriching', 'completed', 'failed'
    processing_error TEXT,

    -- Search optimization
    content_tsvector TSVECTOR,          -- Full-text search index

    CONSTRAINT unique_content_hash UNIQUE(content_hash)
);

-- Indexes
CREATE INDEX idx_content_items_source ON content_items(source);
CREATE INDEX idx_content_items_classification ON content_items(classification);
CREATE INDEX idx_content_items_created_at ON content_items(created_at DESC);
CREATE INDEX idx_content_items_status ON content_items(processing_status);
CREATE INDEX idx_content_items_fts ON content_items USING GIN(content_tsvector);
CREATE INDEX idx_content_items_metadata ON content_items USING GIN(metadata);
```

---

### keywords
**Purpose**: Extracted keywords and entities with weights

```sql
CREATE TABLE keywords (
    id BIGSERIAL PRIMARY KEY,
    item_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    keyword VARCHAR(100) NOT NULL,
    weight FLOAT NOT NULL DEFAULT 1.0,  -- 0.0-1.0, importance/relevance
    keyword_type VARCHAR(50),            -- 'entity', 'concept', 'technology', etc.

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_item_keyword UNIQUE(item_id, keyword)
);

-- Indexes
CREATE INDEX idx_keywords_item_id ON keywords(item_id);
CREATE INDEX idx_keywords_keyword ON keywords(keyword);
CREATE INDEX idx_keywords_weight ON keywords(weight DESC);
```

---

### themes
**Purpose**: High-level themes/topics that span multiple content items

```sql
CREATE TABLE themes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,

    -- Metadata
    color VARCHAR(7),                    -- Hex color for visualization
    icon VARCHAR(50),                    -- Icon identifier

    -- Stats (denormalized for performance)
    item_count INTEGER DEFAULT 0,
    last_mentioned_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_themes_name ON themes(name);
CREATE INDEX idx_themes_last_mentioned ON themes(last_mentioned_at DESC);
```

---

### theme_memberships
**Purpose**: Many-to-many relationship between content items and themes

```sql
CREATE TABLE theme_memberships (
    id BIGSERIAL PRIMARY KEY,
    item_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    theme_id UUID NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    relevance_score FLOAT NOT NULL,      -- 0.0-1.0, how strongly item relates to theme

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_item_theme UNIQUE(item_id, theme_id)
);

-- Indexes
CREATE INDEX idx_theme_memberships_item_id ON theme_memberships(item_id);
CREATE INDEX idx_theme_memberships_theme_id ON theme_memberships(theme_id);
CREATE INDEX idx_theme_memberships_relevance ON theme_memberships(relevance_score DESC);
```

---

## Vector Tables (pgvector)

### embeddings
**Purpose**: Semantic vectors for similarity search

```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id BIGSERIAL PRIMARY KEY,
    item_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,

    -- Vector data
    embedding vector(1536) NOT NULL,     -- OpenAI text-embedding-3-small dimension
    model_version VARCHAR(50) NOT NULL,  -- 'text-embedding-3-small', etc.

    -- Metadata
    chunk_index INTEGER DEFAULT 0,       -- For chunked content (future)

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_item_embedding UNIQUE(item_id, chunk_index)
);

-- Vector similarity index (HNSW for fast approximate search)
CREATE INDEX idx_embeddings_vector ON embeddings
    USING hnsw (embedding vector_cosine_ops);

-- Alternative: IVFFlat index (better for smaller datasets)
-- CREATE INDEX idx_embeddings_vector ON embeddings
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## Graph Tables

### relationships
**Purpose**: Directed edges between content items (graph structure)

```sql
CREATE TABLE relationships (
    id BIGSERIAL PRIMARY KEY,
    from_item_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    to_item_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,

    -- Relationship metadata
    relationship_type VARCHAR(50) NOT NULL,  -- 'references', 'builds_on', 'contradicts', etc.
    strength FLOAT NOT NULL DEFAULT 1.0,     -- 0.0-1.0, confidence/importance

    -- Context
    context TEXT,                            -- Why this relationship exists

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT no_self_reference CHECK (from_item_id != to_item_id),
    CONSTRAINT unique_relationship UNIQUE(from_item_id, to_item_id, relationship_type)
);

-- Indexes
CREATE INDEX idx_relationships_from ON relationships(from_item_id);
CREATE INDEX idx_relationships_to ON relationships(to_item_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
CREATE INDEX idx_relationships_strength ON relationships(strength DESC);

-- Composite index for graph traversal
CREATE INDEX idx_relationships_from_type ON relationships(from_item_id, relationship_type);
```

---

## Supporting Tables

### capture_status
**Purpose**: Track processing status for async enrichment

```sql
CREATE TABLE capture_status (
    capture_id UUID PRIMARY KEY,
    item_id UUID REFERENCES content_items(id) ON DELETE SET NULL,

    status VARCHAR(20) NOT NULL,         -- 'queued', 'enriching', 'completed', 'failed'

    -- Task tracking
    tasks_total INTEGER DEFAULT 6,       -- Total enrichment tasks
    tasks_completed INTEGER DEFAULT 0,   -- How many completed

    -- Errors
    error_message TEXT,
    error_details JSONB,

    -- Timestamps
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_capture_status_status ON capture_status(status);
CREATE INDEX idx_capture_status_queued_at ON capture_status(queued_at DESC);
```

---

### synthetic_content
**Purpose**: System-generated insights (weekly summaries, recommendations, etc.)

```sql
CREATE TABLE synthetic_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    content_type VARCHAR(50) NOT NULL,   -- 'weekly_summary', 'theme_trend', 'recommendation'
    content TEXT NOT NULL,

    -- Source tracking
    source_item_ids UUID[] DEFAULT '{}', -- Which items contributed to this
    time_range_start TIMESTAMP WITH TIME ZONE,
    time_range_end TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_synthetic_content_type ON synthetic_content(content_type);
CREATE INDEX idx_synthetic_content_created ON synthetic_content(created_at DESC);
CREATE INDEX idx_synthetic_content_time_range ON synthetic_content(time_range_start, time_range_end);
```

---

## Schema Statistics

**Total Tables**: 9
- Core: 4 (content_items, keywords, themes, theme_memberships)
- Vector: 1 (embeddings)
- Graph: 1 (relationships)
- Supporting: 3 (capture_status, synthetic_content)

**Estimated Storage** (10,000 items):
- content_items: ~50-100 MB (depends on content length)
- keywords: ~5 MB
- embeddings: ~60 MB (1536 dimensions × 4 bytes × 10k)
- relationships: ~5 MB
- Other: ~10 MB
- **Total**: ~150-200 MB

**Performance Targets**:
- Insert content item: <10ms
- Vector similarity search (top-20): <100ms
- Graph traversal (2 hops): <50ms
- Full-text search: <100ms

---

## Migration Strategy

**Tool**: Alembic (SQLAlchemy migrations)

**Migration Order**:
1. Core tables (content_items, keywords, themes, theme_memberships)
2. pgvector extension + embeddings table
3. Graph tables (relationships)
4. Supporting tables (capture_status, synthetic_content)
5. Indexes (can be created concurrently)

**Rollback Support**: All migrations reversible for first 5 versions.

---

**Last Updated**: 2026-01-12
