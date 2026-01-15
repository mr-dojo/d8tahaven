"""OpenAI embeddings integration with error handling and retries."""

import os
import time
from typing import List, Optional

import structlog
from openai import OpenAI, APIError, RateLimitError, APIConnectionError

logger = structlog.get_logger()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds

# Singleton OpenAI client (avoid creating new client per request)
_openai_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Get or create the OpenAI client singleton."""
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please add it to your .env file."
            )
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


class EmbeddingError(Exception):
    """Raised when embedding generation fails after retries."""
    pass


def generate_embedding(
    text: str,
    model: str = EMBEDDING_MODEL,
    max_retries: int = MAX_RETRIES
) -> List[float]:
    """
    Generate embedding for text using OpenAI API with retry logic.

    Args:
        text: Text to embed (will be truncated if too long)
        model: OpenAI model to use (default: text-embedding-3-small)
        max_retries: Maximum number of retry attempts

    Returns:
        List of floats representing the embedding vector (1536 dimensions)

    Raises:
        EmbeddingError: If embedding generation fails after all retries
        ValueError: If OPENAI_API_KEY is not set

    Example:
        >>> embedding = generate_embedding("Hello world")
        >>> len(embedding)
        1536
    """
    # Truncate text if too long (OpenAI limit is ~8191 tokens, ~32k chars is safe)
    max_chars = 32000
    if len(text) > max_chars:
        text = text[:max_chars]
        logger.warning(
            "text_truncated",
            original_length=len(text),
            truncated_length=max_chars
        )

    client = _get_client()
    retry_delay = INITIAL_RETRY_DELAY

    for attempt in range(max_retries):
        try:
            logger.debug(
                "generating_embedding",
                attempt=attempt + 1,
                model=model,
                text_length=len(text)
            )

            response = client.embeddings.create(
                input=text,
                model=model
            )

            embedding = response.data[0].embedding

            # Verify dimensions
            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise EmbeddingError(
                    f"Unexpected embedding dimensions: {len(embedding)} "
                    f"(expected {EMBEDDING_DIMENSIONS})"
                )

            logger.info(
                "embedding_generated",
                model=model,
                dimensions=len(embedding),
                text_length=len(text)
            )

            return embedding

        except RateLimitError as e:
            logger.warning(
                "rate_limit_error",
                attempt=attempt + 1,
                retry_delay=retry_delay,
                error=str(e)
            )

            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise EmbeddingError(
                    f"Rate limit exceeded after {max_retries} attempts: {e}"
                )

        except APIConnectionError as e:
            logger.warning(
                "api_connection_error",
                attempt=attempt + 1,
                retry_delay=retry_delay,
                error=str(e)
            )

            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise EmbeddingError(
                    f"API connection failed after {max_retries} attempts: {e}"
                )

        except APIError as e:
            logger.error(
                "api_error",
                attempt=attempt + 1,
                error=str(e),
                status_code=getattr(e, 'status_code', None)
            )

            # Don't retry on client errors (4xx)
            if hasattr(e, 'status_code') and 400 <= e.status_code < 500:
                raise EmbeddingError(f"API error: {e}")

            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise EmbeddingError(
                    f"API error after {max_retries} attempts: {e}"
                )

        except Exception as e:
            logger.error(
                "unexpected_error",
                attempt=attempt + 1,
                error=str(e),
                error_type=type(e).__name__
            )
            raise EmbeddingError(f"Unexpected error generating embedding: {e}")

    # Should never reach here
    raise EmbeddingError("Failed to generate embedding (unknown error)")


def get_model_version() -> str:
    """
    Get the current embedding model version.

    Returns:
        String identifier for the embedding model
    """
    return EMBEDDING_MODEL


def get_embedding_dimensions() -> int:
    """
    Get the number of dimensions for the current embedding model.

    Returns:
        Integer number of dimensions (1536 for text-embedding-3-small)
    """
    return EMBEDDING_DIMENSIONS
