# Database Schema - V1

**Scope**: Minimum viable schema for capture and retrieval.
**Database**: PostgreSQL 16 with pgvector extension
**ORM**: SQLAlchemy 2.0+

---

## Overview

V1 uses **2 tables**:
1. **content_items** - Stores captured content
2. **embeddings** - Stores OpenAI vectors for semantic search

**What's NOT in V1**: keywords, themes, relationships, synthetic_content, capture_status tables (deferred to v2).

---

## Table: content_items

Primary storage for all captured content (text or file-extracted).

```sql
CREATE TABLE content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    captured_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT content_not_empty CHECK (length(trim(content)) > 0)
);

-- Indexes
CREATE INDEX idx_content_items_created_at ON content_items(created_at DESC);
CREATE INDEX idx_content_items_source ON content_items(source);
CREATE INDEX idx_content_items_content_hash ON content_items(content_hash);
```

### Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `content` | TEXT | Raw captured text | NOT NULL, non-empty |
| `content_hash` | VARCHAR(64) | SHA-256 hash of content | UNIQUE, for deduplication |
| `source` | VARCHAR(100) | Source identifier | NOT NULL (e.g., "browser_extension") |
| `metadata` | JSONB | User metadata (flexible) | Optional, defaults to `{}` |
| `created_at` | TIMESTAMPTZ | Server creation time | Auto-generated |
| `captured_at` | TIMESTAMPTZ | User capture time | Optional (may differ from created_at) |

### Source Values (Convention)

- `"manual_entry"` - Direct API call
- `"browser_extension"` - From browser plugin
- `"file_upload"` - Extracted from uploaded file
- `"quick_note"` - Simple text capture
- `"api"` - Generic API usage

### Metadata Schema (Flexible)

Common metadata patterns:
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "tags": ["research", "ai"],
  "filename": "document.pdf",
  "file_size": 245678,
  "note": "Important context"
}
```

**No schema validation in v1** - JSONB field accepts any valid JSON.

---

## Table: embeddings

Stores OpenAI embedding vectors for semantic search.

```sql
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_item_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    embedding_vector vector(1536) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT one_embedding_per_item UNIQUE(content_item_id)
);

-- Vector index for fast similarity search
CREATE INDEX idx_embeddings_vector ON embeddings
USING hnsw (embedding_vector vector_cosine_ops);

-- Foreign key index
CREATE INDEX idx_embeddings_content_item_id ON embeddings(content_item_id);
```

### Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Primary key | Auto-generated |
| `content_item_id` | UUID | Foreign key to content_items | NOT NULL, CASCADE delete |
| `embedding_vector` | vector(1536) | OpenAI embedding | NOT NULL, 1536 dimensions |
| `model_version` | VARCHAR(50) | Embedding model used | NOT NULL (e.g., "text-embedding-3-small") |
| `created_at` | TIMESTAMPTZ | Generation timestamp | Auto-generated |

### Embedding Details

**Model**: OpenAI `text-embedding-3-small`
**Dimensions**: 1536
**Distance Metric**: Cosine similarity (via `vector_cosine_ops`)

**HNSW Index**: Hierarchical Navigable Small World graph for fast approximate nearest neighbor search.
- Trade-off: Slightly less accurate than exact search, but 100x faster
- Good for >1000 vectors

---

## Relationships

```
content_items (1) ←──── (1) embeddings
```

**One-to-one**: Each content item has exactly one embedding.

**Cascade**: Deleting a content_item automatically deletes its embedding.

---

## SQLAlchemy Models

### ContentItem Model

```python
from sqlalchemy import Column, String, Text, TIMESTAMP, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True, nullable=False)
    source = Column(String(100), nullable=False)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationship
    embedding = relationship("Embedding", back_populates="content_item", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("length(trim(content)) > 0", name="content_not_empty"),
    )
```

### Embedding Model

```python
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_item_id = Column(UUID(as_uuid=True), ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, unique=True)
    embedding_vector = Column(Vector(1536), nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationship
    content_item = relationship("ContentItem", back_populates="embedding")
```

---

## Migration (Alembic)

### Initial Migration

```python
"""Initial schema - content_items and embeddings

Revision ID: 001
Create Date: 2026-01-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create content_items table
    op.create_table(
        'content_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('captured_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("length(trim(content)) > 0", name='content_not_empty')
    )

    # Indexes for content_items
    op.create_index('idx_content_items_created_at', 'content_items', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_content_items_source', 'content_items', ['source'])
    op.create_index('idx_content_items_content_hash', 'content_items', ['content_hash'], unique=True)

    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding_vector', postgresql.ARRAY(sa.Float()), nullable=False),  # pgvector type
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('content_item_id', name='one_embedding_per_item')
    )

    # Indexes for embeddings
    op.create_index('idx_embeddings_content_item_id', 'embeddings', ['content_item_id'])
    op.execute('CREATE INDEX idx_embeddings_vector ON embeddings USING hnsw (embedding_vector vector_cosine_ops)')

def downgrade():
    op.drop_table('embeddings')
    op.drop_table('content_items')
    op.execute('DROP EXTENSION IF EXISTS vector')
```

---

## Common Queries

### Insert content with embedding

```python
from sqlalchemy.orm import Session
import hashlib

def capture_content(db: Session, content: str, source: str, embedding: list[float]) -> ContentItem:
    # Calculate hash for deduplication
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check if already exists
    existing = db.query(ContentItem).filter_by(content_hash=content_hash).first()
    if existing:
        return existing

    # Create new content item
    item = ContentItem(
        content=content,
        content_hash=content_hash,
        source=source
    )
    db.add(item)
    db.flush()  # Get item.id

    # Create embedding
    emb = Embedding(
        content_item_id=item.id,
        embedding_vector=embedding,
        model_version="text-embedding-3-small"
    )
    db.add(emb)
    db.commit()

    return item
```

### Semantic search

```python
from sqlalchemy import func

def semantic_search(db: Session, query_embedding: list[float], limit: int = 5) -> list[dict]:
    results = (
        db.query(
            ContentItem,
            Embedding.embedding_vector.cosine_distance(query_embedding).label("distance")
        )
        .join(Embedding)
        .order_by("distance")
        .limit(limit)
        .all()
    )

    return [
        {
            "capture_id": str(item.id),
            "content": item.content,
            "similarity_score": 1 - distance,  # Convert distance to similarity
            "created_at": item.created_at.isoformat(),
            "metadata": item.metadata
        }
        for item, distance in results
    ]
```

### Recent items

```python
def get_recent_items(db: Session, limit: int = 20, offset: int = 0) -> list[ContentItem]:
    return (
        db.query(ContentItem)
        .order_by(ContentItem.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
```

---

## pgvector Setup

### Install Extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Verify**:
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Vector Operations

**Distance metrics**:
- `<->` - Euclidean distance (L2)
- `<#>` - Negative inner product
- `<=>` - Cosine distance (1 - cosine similarity)

**For embeddings, use cosine distance**: `embedding_vector <=> query_vector`

---

## Performance Notes

### HNSW Index Parameters

```sql
CREATE INDEX idx_embeddings_vector ON embeddings
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Parameters**:
- `m`: Max connections per layer (default 16, higher = more accurate but slower)
- `ef_construction`: Size of candidate list during index build (default 64)

**V1 uses defaults** - optimize later if needed.

### Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Insert item + embedding | ~50ms | Single DB transaction |
| Semantic search (1000 items) | ~10ms | HNSW approximate search |
| Semantic search (10K items) | ~20ms | Scales sublinearly |
| Recent items | ~5ms | Simple index scan |

---

## Data Retention (V1: Unlimited)

**V1**: No automatic cleanup. All captures stored indefinitely.

**V2+**: Optional retention policies (e.g., delete items older than 1 year).

---

## Backup Recommendations

**PostgreSQL**:
```bash
pg_dump -U pdc_user -d pdc > backup_$(date +%Y%m%d).sql
```

**Frequency**: Daily (automate with cron).

---

## Future Schema Changes (V2+)

Tables deferred to v2:
- `keywords` - Extracted keywords with weights
- `themes` - High-level topics
- `relationships` - Graph edges between items
- `synthetic_content` - AI-generated summaries
- `capture_status` - Async processing tracking

See `docs/data-models/schema-overview.md` for full schema vision.
