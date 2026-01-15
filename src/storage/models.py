"""SQLAlchemy models for content storage."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, TIMESTAMP, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from src.storage.database import Base


class ContentItem(Base):
    """
    Stores captured content (text or file-extracted).

    Attributes:
        id: Unique identifier (UUID)
        content: Raw captured text
        content_hash: SHA-256 hash for deduplication
        source: Source identifier (e.g., 'browser_extension', 'manual_entry')
        meta: Flexible JSONB field for user metadata (stored as 'metadata' in DB)
        created_at: Server creation timestamp
        captured_at: User-provided capture timestamp (optional)
        embedding: One-to-one relationship with Embedding
    """
    __tablename__ = "content_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True, nullable=False)
    source = Column(String(100), nullable=False)
    meta = Column("metadata", JSONB, default={}, nullable=False)  # Column name 'metadata', attribute 'meta'
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationship to embedding (one-to-one)
    embedding = relationship(
        "Embedding",
        back_populates="content_item",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("length(trim(content)) > 0", name="content_not_empty"),
    )

    def __repr__(self):
        return f"<ContentItem(id={self.id}, source='{self.source}', created_at={self.created_at})>"


class Embedding(Base):
    """
    Stores OpenAI embedding vectors for semantic search.

    Attributes:
        id: Unique identifier (UUID)
        content_item_id: Foreign key to content_items
        embedding_vector: 1536-dimensional vector (text-embedding-3-small)
        model_version: Embedding model identifier
        created_at: Generation timestamp
        content_item: Relationship back to ContentItem
    """
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False
    )
    embedding_vector = Column(Vector(1536), nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationship to content_item
    content_item = relationship(
        "ContentItem",
        back_populates="embedding"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("content_item_id", name="one_embedding_per_item"),
    )

    def __repr__(self):
        return f"<Embedding(id={self.id}, content_item_id={self.content_item_id}, model={self.model_version})>"
