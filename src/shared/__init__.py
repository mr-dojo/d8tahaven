"""Shared utilities and integrations."""

from src.shared.embeddings import (
    generate_embedding,
    get_model_version,
    get_embedding_dimensions,
    EmbeddingError,
)

__all__ = [
    "generate_embedding",
    "get_model_version",
    "get_embedding_dimensions",
    "EmbeddingError",
]
