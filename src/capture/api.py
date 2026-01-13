from fastapi import FastAPI, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid

from src.capture.file_extractor import extract_text, SUPPORTED_EXTENSIONS, MAX_FILE_SIZE

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
    queued_at: datetime


class FileCaptureResponse(BaseModel):
    capture_id: str
    status: str
    filename: str
    file_size: int
    extracted_text_preview: str
    queued_at: datetime


@app.post("/v1/capture", status_code=status.HTTP_201_CREATED, response_model=CaptureResponse)
async def capture_content(request: CaptureRequest):
    capture_id = str(uuid.uuid4())
    return CaptureResponse(
        capture_id=capture_id,
        status="queued",
        queued_at=datetime.utcnow()
    )


@app.post("/v1/capture/file", status_code=status.HTTP_201_CREATED, response_model=FileCaptureResponse)
async def capture_file(file: UploadFile = File(...)):
    # Validate file extension
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Validate file size
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Extract text
    try:
        extracted_text = extract_text(file.filename, file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text: {str(e)}"
        )
    
    # Validate extracted content
    if not extracted_text or not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Extracted text is empty"
        )
    
    capture_id = str(uuid.uuid4())
    
    return FileCaptureResponse(
        capture_id=capture_id,
        status="queued",
        filename=file.filename,
        file_size=len(file_content),
        extracted_text_preview=extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
        queued_at=datetime.utcnow()
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}
