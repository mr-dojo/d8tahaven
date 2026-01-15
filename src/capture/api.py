from fastapi import FastAPI, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import hashlib
import structlog

from src.storage import get_db, ContentItem, Embedding
from src.shared import generate_embedding, get_model_version, EmbeddingError
from src.capture.file_extractor import (
    extract_text,
    ExtractionError,
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE
)

logger = structlog.get_logger()

app = FastAPI()

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


class FileCaptureResponse(BaseModel):
    capture_id: str
    status: str
    filename: str
    file_size: int
    content_type: str
    extracted_text_preview: str
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

@app.post("/v1/capture/file", status_code=status.HTTP_201_CREATED, response_model=FileCaptureResponse)
async def capture_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Capture content from an uploaded file (PDF, DOCX, TXT).

    V1 implementation: Synchronous (2-5 second response time depending on file size).
    - Validates file type and size
    - Extracts text from file (with encoding detection for TXT)
    - Calculates SHA-256 hash for deduplication
    - Checks for existing content (returns existing if found)
    - Generates OpenAI embedding
    - Saves ContentItem + Embedding to database
    - Returns capture_id with file metadata

    Supported file types: .pdf, .docx, .txt
    Maximum file size: 10MB

    Raises:
        HTTPException 413: If file exceeds 10MB
        HTTPException 415: If file type is not supported
        HTTPException 422: If text extraction fails or extracted text is empty
        HTTPException 500: If embedding generation or database save fails
    """
    # Validate file extension
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    logger.info("file_upload_received", filename=file.filename, size=file_size, extension=ext)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({file_size // (1024*1024)}MB). Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Extract text from file
    try:
        extracted_text = extract_text(file.filename, file_content)
    except ExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e)
        )

    # Validate extracted content
    if not extracted_text or not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Extracted text is empty. The file may be blank or contain only images."
        )

    extracted_text = extracted_text.strip()

    try:
        # Calculate content hash for deduplication
        content_hash = hashlib.sha256(extracted_text.encode('utf-8')).hexdigest()

        # Check if content already exists
        existing_item = db.query(ContentItem).filter_by(content_hash=content_hash).first()
        if existing_item:
            logger.info("duplicate_file_content", capture_id=str(existing_item.id), filename=file.filename)
            return FileCaptureResponse(
                capture_id=str(existing_item.id),
                status="completed",
                filename=file.filename,
                file_size=file_size,
                content_type=ext,
                extracted_text_preview=extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
                created_at=existing_item.created_at
            )

        # Generate embedding (this takes 2-3 seconds)
        try:
            embedding_vector = generate_embedding(extracted_text)
        except EmbeddingError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate embedding: {str(e)}"
            )

        # Create content item with file metadata
        content_item = ContentItem(
            content=extracted_text,
            content_hash=content_hash,
            source="file_upload",
            meta={
                "filename": file.filename,
                "file_size": file_size,
                "content_type": ext,
                "original_content_type": file.content_type
            }
        )
        db.add(content_item)
        db.flush()

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

        logger.info(
            "file_captured",
            capture_id=str(content_item.id),
            filename=file.filename,
            text_length=len(extracted_text)
        )

        return FileCaptureResponse(
            capture_id=str(content_item.id),
            status="completed",
            filename=file.filename,
            file_size=file_size,
            content_type=ext,
            extracted_text_preview=extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
            created_at=content_item.created_at
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error("file_capture_failed", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file capture: {str(e)}"
        )


@app.get("/health")
async def health_check():
    return {"status": "ok"}
