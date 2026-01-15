"""Initial schema - content_items and embeddings

Revision ID: 8bea1da7f861
Revises:
Create Date: 2026-01-15 03:08:38.121120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '8bea1da7f861'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create content_items and embeddings tables."""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create content_items table
    op.create_table(
        'content_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('captured_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("length(trim(content)) > 0", name='content_not_empty'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash')
    )

    # Create indexes for content_items
    op.create_index('idx_content_items_created_at', 'content_items', [sa.text('created_at DESC')], unique=False)
    op.create_index('idx_content_items_source', 'content_items', ['source'], unique=False)

    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding_vector', Vector(1536), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_item_id', name='one_embedding_per_item')
    )

    # Create indexes for embeddings
    op.create_index('idx_embeddings_content_item_id', 'embeddings', ['content_item_id'], unique=False)

    # Create HNSW index for vector similarity search
    op.execute('CREATE INDEX idx_embeddings_vector ON embeddings USING hnsw (embedding_vector vector_cosine_ops)')


def downgrade() -> None:
    """Drop content_items and embeddings tables."""
    op.drop_table('embeddings')
    op.drop_table('content_items')
    op.execute('DROP EXTENSION IF EXISTS vector')
