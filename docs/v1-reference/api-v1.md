# API Reference - V1 Endpoints

**Scope**: Minimum viable API for capture and retrieval.
**Base URL**: `http://localhost:8000`

---

## Capture Endpoints

### POST /v1/capture

Capture text content with automatic embedding generation.

**Request**:
```json
{
  "content": "Remember to buy milk tomorrow morning",
  "source": "quick_note",
  "metadata": {
    "url": "https://example.com",
    "title": "Optional page title"
  }
}
```

**Fields**:
- `content` (string, required): Text to capture. Cannot be empty/whitespace only. Max 100,000 characters.
- `source` (string, required): Source identifier (e.g., "manual_entry", "browser_extension", "api")
- `metadata` (object, optional): User-provided metadata (URL, title, tags, etc.)

**Response** (201 Created):
```json
{
  "capture_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2026-01-13T10:30:00Z"
}
```

**Behavior**:
- Generates SHA-256 hash for deduplication
- If content already exists, returns existing capture_id
- Generates OpenAI embedding (synchronous, 2-3 second response)
- Stores content + embedding in database
- Returns immediately after persistence

**Errors**:
- `422 Unprocessable Entity`: Content empty/missing or validation failed
- `500 Internal Server Error`: OpenAI API failure or database error

---

### POST /v1/capture/file

Upload file (PDF/DOCX/TXT), extract text, and capture.

**Request**: `multipart/form-data`
- `file`: File upload (required)
- `source`: String (optional, defaults to "file_upload")
- `metadata`: JSON string (optional)

**Example**:
```bash
curl -X POST http://localhost:8000/v1/capture/file \
  -F "file=@research-notes.pdf" \
  -F "source=pdf_upload" \
  -F 'metadata={"category": "research"}'
```

**Response** (201 Created):
```json
{
  "capture_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "filename": "research-notes.pdf",
  "file_size": 245678,
  "extracted_text_preview": "Introduction to context collection systems..."
}
```

**Supported Formats**:
- **PDF**: Extracted via pypdf library
- **DOCX**: Extracted via python-docx library
- **TXT**: Read directly

**Limits**:
- Max file size: 10 MB
- Max extracted text: 100,000 characters (truncated if longer)

**Errors**:
- `400 Bad Request`: No file provided or unsupported format
- `413 Payload Too Large`: File exceeds 10 MB
- `422 Unprocessable Entity`: Text extraction failed
- `500 Internal Server Error`: Processing failure

---

## Retrieval Endpoints

### POST /v1/retrieve/semantic

Semantic search using vector similarity (cosine distance).

**Request**:
```json
{
  "query": "What did I learn about context collection?",
  "limit": 5
}
```

**Fields**:
- `query` (string, required): Search query text
- `limit` (integer, optional): Number of results (default: 5, max: 50)

**Response** (200 OK):
```json
{
  "results": [
    {
      "capture_id": "550e8400-e29b-41d4-a716-446655440000",
      "content": "Context collection systems help AI remember...",
      "source": "browser_extension",
      "similarity_score": 0.87,
      "created_at": "2026-01-13T10:30:00Z",
      "metadata": {
        "url": "https://example.com/article",
        "title": "Context Systems Overview"
      }
    },
    {
      "capture_id": "660e8400-e29b-41d4-a716-446655440001",
      "content": "Personal data collection requires...",
      "source": "manual_entry",
      "similarity_score": 0.82,
      "created_at": "2026-01-12T15:20:00Z",
      "metadata": {}
    }
  ],
  "query": "What did I learn about context collection?",
  "count": 2
}
```

**Behavior**:
- Generates embedding for query text
- Performs pgvector cosine similarity search
- Returns results ordered by similarity (highest first)
- Similarity score range: 0.0 (unrelated) to 1.0 (identical)

**Errors**:
- `422 Unprocessable Entity`: Query empty or invalid
- `500 Internal Server Error`: OpenAI API or database failure

---

### GET /v1/retrieve/recent

Retrieve recently captured items (simple time-ordered list).

**Request**:
```
GET /v1/retrieve/recent?limit=20&offset=0
```

**Query Parameters**:
- `limit` (integer, optional): Number of results (default: 20, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "results": [
    {
      "capture_id": "550e8400-e29b-41d4-a716-446655440000",
      "content": "Remember to buy milk tomorrow morning",
      "source": "quick_note",
      "created_at": "2026-01-13T10:30:00Z",
      "metadata": {}
    },
    {
      "capture_id": "660e8400-e29b-41d4-a716-446655440001",
      "content": "Meeting notes from product sync...",
      "source": "manual_entry",
      "created_at": "2026-01-13T09:15:00Z",
      "metadata": {
        "tags": ["meeting", "product"]
      }
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 47
}
```

**Behavior**:
- Returns items ordered by `created_at` DESC (newest first)
- Includes full content (no truncation)
- No similarity scoring (simple chronological list)

---

## Health Check

### GET /health

Simple health check endpoint.

**Response** (200 OK):
```json
{
  "status": "ok"
}
```

---

## Common Response Patterns

### Success Responses
- **201 Created**: Resource created (capture endpoints)
- **200 OK**: Request successful (retrieval endpoints)

### Error Responses
- **400 Bad Request**: Invalid request format
- **413 Payload Too Large**: File/content exceeds limits
- **422 Unprocessable Entity**: Validation failed
- **500 Internal Server Error**: Server-side failure

**Error Format**:
```json
{
  "detail": "Content cannot be empty or whitespace only"
}
```

---

## Authentication (V1: Optional)

**V1 Deployment**: Local development only, no authentication required.

**V1.1+ (Future)**: API key authentication via `X-API-Key` header.

---

## Rate Limiting (V1: Not Implemented)

**V1**: No rate limiting (local development).

**V2**: 100 requests/minute per API key.

---

## CORS Configuration

**Allowed Origins** (configured in `.env`):
```
CORS_ORIGINS=["http://localhost:3000", "chrome-extension://*"]
```

Permits browser extension and local frontend development.

---

## Notes

- All timestamps are ISO 8601 format (UTC)
- All IDs are UUIDv4
- Content truncation only occurs in `extracted_text_preview` (file uploads)
- Embedding generation is synchronous in v1 (2-3 second response time)
- No partial success: operations are atomic (all-or-nothing)
