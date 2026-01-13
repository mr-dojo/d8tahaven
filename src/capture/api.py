from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid

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

@app.post("/v1/capture", status_code=status.HTTP_201_CREATED, response_model=CaptureResponse)
async def capture_content(request: CaptureRequest):
    # Determine capture_id (in real app, this might come from DB)
    capture_id = str(uuid.uuid4())
    
    # In a real app, we would enqueue the task here (Celery/Redis)
    # For now, we simulate success
    
    return CaptureResponse(
        capture_id=capture_id,
        status="queued",
        queued_at=datetime.utcnow()
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
