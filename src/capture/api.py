import hashlib
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.storage import get_db, ContentItem, Embedding
from src.shared import generate_embedding, get_model_version, EmbeddingError

app = FastAPI()

# CORS configuration for browser extension
cors_origins = os.getenv("CORS_ORIGINS", "chrome-extension://*,moz-extension://*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class CaptureRequest(BaseModel):
    content: str = Field(..., description="The content to capture")
    source: str = Field(..., description="Source of the content")
    metadata: Optional[dict] = Field(default_factory=dict, description="Optional metadata")

    @field_validator('content')
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        return v.strip()

class CaptureResponse(BaseModel):
    capture_id: str
    status: str
    created_at: datetime

@app.post("/v1/capture", status_code=status.HTTP_201_CREATED, response_model=CaptureResponse)
async def capture_content(request: CaptureRequest, db: Session = Depends(get_db)):
    """
    Capture content with automatic embedding generation.

    V1 implementation: Synchronous (2-3 second response time).
    - Calculates SHA-256 hash for deduplication
    - Checks for existing content (returns existing if found)
    - Generates OpenAI embedding
    - Saves ContentItem + Embedding to database
    - Returns capture_id

    Raises:
        HTTPException 500: If embedding generation or database save fails
    """
    try:
        # Calculate content hash for deduplication
        content_hash = hashlib.sha256(request.content.encode('utf-8')).hexdigest()

        # Check if content already exists
        existing_item = db.query(ContentItem).filter_by(content_hash=content_hash).first()
        if existing_item:
            return CaptureResponse(
                capture_id=str(existing_item.id),
                status="completed",
                created_at=existing_item.created_at
            )

        # Generate embedding (this takes 2-3 seconds)
        try:
            embedding_vector = generate_embedding(request.content)
        except EmbeddingError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate embedding: {str(e)}"
            )

        # Create content item
        content_item = ContentItem(
            content=request.content,
            content_hash=content_hash,
            source=request.source,
            meta=request.metadata or {}
        )
        db.add(content_item)
        db.flush()  # Get the ID without committing yet

        # Create embedding
        embedding = Embedding(
            content_item_id=content_item.id,
            embedding_vector=embedding_vector,
            model_version=get_model_version()
        )
        db.add(embedding)

        # Commit both together (atomic)
        db.commit()
        db.refresh(content_item)

        return CaptureResponse(
            capture_id=str(content_item.id),
            status="completed",
            created_at=content_item.created_at
        )

    except IntegrityError:
        # Race condition: another request inserted the same content
        db.rollback()
        existing_item = db.query(ContentItem).filter_by(content_hash=content_hash).first()
        if existing_item:
            return CaptureResponse(
                capture_id=str(existing_item.id),
                status="completed",
                created_at=existing_item.created_at
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save capture: database constraint violation"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save capture: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
