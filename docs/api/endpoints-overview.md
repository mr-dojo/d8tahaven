# API Endpoints Overview

**Framework**: FastAPI
**Base URL**: `/v1` (version prefix for future API evolution)
**Authentication**: API key (header: `X-API-Key`)
**Response Format**: JSON

---

## Endpoint Organization

Endpoints are organized by the five system stages:

1. **Capture** (`/v1/capture/*`) - Capture content
2. **Retrieval** (`/v1/retrieve/*`) - Query and package context
3. **Intelligence** (`/v1/insights/*`) - Access synthesized insights
4. **Management** (`/v1/manage/*`) - Admin operations

*(Enrichment and Storage are internal—no direct API exposure)*

---

## Stage 1: Capture API

### POST /v1/capture
**Purpose**: Capture text content

**Request**:
```json
{
  "content": "This is my note about AI agents and context collection",
  "source": "manual_entry",
  "captured_at": "2024-01-15T14:30:00Z",  // optional, defaults to now
  "metadata": {                            // optional
    "project": "Phoenix",
    "urgent": true,
    "tags": ["ai", "agents"]
  }
}
```

**Response** (201 Created):
```json
{
  "capture_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "queued_at": "2024-01-15T14:30:01.234Z",
  "estimated_completion": "2024-01-15T14:30:30Z"
}
```

**Performance**: <100ms response time

---

### POST /v1/capture/file
**Purpose**: Upload file (PDF, DOCX, TXT)

**Request** (multipart/form-data):
```
Content-Type: multipart/form-data

file: [binary file data]
source: "file_upload"
metadata: {"project": "Research"}
```

**Response** (201 Created):
```json
{
  "capture_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "queued",
  "filename": "research-notes.pdf",
  "file_size": 245678,
  "extracted_text_preview": "Introduction to context collection..."
}
```

**Limits**:
- Max file size: 10 MB
- Supported formats: PDF, DOCX, TXT
- Text extraction timeout: 30 seconds

---

### GET /v1/status/{capture_id}
**Purpose**: Check processing status

**Response** (200 OK):
```json
{
  "capture_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "enriching",
  "progress": {
    "tasks_total": 6,
    "tasks_completed": 3,
    "current_task": "theme_detection"
  },
  "queued_at": "2024-01-15T14:30:01Z",
  "started_at": "2024-01-15T14:30:02Z",
  "estimated_completion": "2024-01-15T14:30:30Z"
}
```

**Possible Statuses**:
- `queued` - Waiting for worker
- `enriching` - LLM processing in progress
- `completed` - Stored and ready for retrieval
- `failed` - Error occurred (see error_message)

---

### GET /v1/capture/recent
**Purpose**: List recently captured items

**Query Parameters**:
- `limit` (default: 20, max: 100)
- `offset` (default: 0)
- `source` (filter by source)

**Response** (200 OK):
```json
{
  "items": [
    {
      "capture_id": "...",
      "status": "completed",
      "content_preview": "This is my note about...",
      "source": "manual_entry",
      "captured_at": "2024-01-15T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 1234,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

---

## Stage 4: Retrieval API

### POST /v1/retrieve/semantic
**Purpose**: Semantic search via vector similarity

**Request**:
```json
{
  "query": "What have I learned about AI agent architecture?",
  "limit": 20,
  "filters": {
    "classification": ["note", "reference"],
    "date_range": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    },
    "themes": ["AI", "Software Architecture"]
  },
  "min_similarity": 0.7
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "item_id": "...",
      "content": "Notes on multi-agent systems...",
      "similarity_score": 0.92,
      "classification": "note",
      "keywords": ["agents", "architecture", "coordination"],
      "themes": ["AI", "Software Architecture"],
      "captured_at": "2024-01-15T10:00:00Z"
    }
  ],
  "query_metadata": {
    "query_embedding_time_ms": 45,
    "search_time_ms": 87,
    "total_candidates": 1523,
    "returned_count": 20
  }
}
```

**Performance**: <500ms response time

---

### GET /v1/retrieve/temporal
**Purpose**: Time-based retrieval

**Query Parameters**:
- `date_range` (e.g., "last_week", "last_month", or ISO dates)
- `limit` (default: 20)
- `classification` (filter)

**Response** (200 OK):
```json
{
  "results": [...],
  "time_range": {
    "start": "2024-01-08T00:00:00Z",
    "end": "2024-01-15T23:59:59Z",
    "description": "Last 7 days"
  }
}
```

---

### POST /v1/retrieve/context
**Purpose**: Package context for LLM agent prompts (primary endpoint for browser plugin GET mode)

**Request**:
```json
{
  "agent_query": "I'm working on the Phoenix project. What's relevant?",
  "context_requirements": {
    "diversity": true,              // Include varied content types
    "recency_weight": 0.7,          // How much to favor recent items (0.0-1.0)
    "max_tokens": 4000,             // Token budget for context
    "include_relationships": true   // Include related items
  },
  "filters": {
    "metadata.project": "Phoenix"
  }
}
```

**Response** (200 OK):
```json
{
  "context": {
    "formatted_markdown": "# Relevant Context\n\n## Recent Notes\n...",
    "formatted_json": [...],
    "token_count": 3847
  },
  "items_included": [
    {
      "item_id": "...",
      "relevance_score": 0.95,
      "reason": "High semantic similarity + recent mention"
    }
  ],
  "metadata": {
    "retrieval_strategy": "semantic + temporal + graph",
    "deduplication_removed": 3
  }
}
```

**Browser Plugin Usage**:
```javascript
// Browser extension GET mode simplified request
{
  "query": "Help me write about data sovereignty",  // User's current prompt
  "max_tokens": 4000,
  "format": "markdown"  // Returns formatted_markdown directly
}
```

**Performance**: <500ms response time

---

### GET /v1/retrieve/item/{item_id}
**Purpose**: Get single item with all metadata

**Response** (200 OK):
```json
{
  "item_id": "...",
  "content": "Full content here...",
  "classification": "note",
  "summary": "Brief summary...",
  "keywords": [...],
  "themes": [...],
  "relationships": {
    "references": [...],
    "referenced_by": [...],
    "builds_on": [...]
  },
  "metadata": {...},
  "captured_at": "2024-01-15T14:30:00Z",
  "created_at": "2024-01-15T14:30:01Z"
}
```

---

## Stage 5: Intelligence API

### GET /v1/insights/weekly-summary
**Purpose**: Get latest weekly synthesis

**Query Parameters**:
- `week_offset` (default: 0, i.e., current week; 1 = last week)

**Response** (200 OK):
```json
{
  "summary": "This week you focused heavily on AI agent architecture...",
  "week_range": {
    "start": "2024-01-08T00:00:00Z",
    "end": "2024-01-14T23:59:59Z"
  },
  "highlights": [
    {
      "content": "Breakthrough on multi-agent coordination...",
      "item_id": "...",
      "importance_score": 0.95
    }
  ],
  "top_themes": [
    {"theme": "AI", "item_count": 23, "trend": "increasing"},
    {"theme": "Software Architecture", "item_count": 15, "trend": "stable"}
  ]
}
```

---

### GET /v1/insights/theme-trends
**Purpose**: Get theme evolution over time

**Query Parameters**:
- `time_range` (default: "last_90_days")

**Response** (200 OK):
```json
{
  "themes": [
    {
      "theme": "AI",
      "trend": "increasing",
      "mentions_current_period": 45,
      "mentions_previous_period": 28,
      "growth_rate": 0.61,
      "first_mentioned": "2023-11-15T10:00:00Z",
      "last_mentioned": "2024-01-15T16:30:00Z"
    }
  ]
}
```

---

### GET /v1/insights/gaps
**Purpose**: Identify neglected areas

**Response** (200 OK):
```json
{
  "gaps": [
    {
      "type": "project",
      "name": "Mobile App Redesign",
      "last_activity": "2023-12-01T10:00:00Z",
      "days_since_activity": 45,
      "prior_importance": 0.85,
      "recommendation": "No captures in 45 days. Consider reviewing or archiving."
    }
  ]
}
```

---

### GET /v1/insights/recommendations
**Purpose**: System-generated recommendations

**Response** (200 OK):
```json
{
  "recommendations": [
    {
      "type": "connection",
      "title": "Connect related ideas",
      "description": "Your notes on 'agent coordination' and 'distributed systems' seem related.",
      "items": ["...", "..."],
      "confidence": 0.87
    },
    {
      "type": "next_action",
      "title": "Follow up on Phoenix project",
      "description": "You mentioned needing to 'test the API' 3 days ago.",
      "item_id": "...",
      "confidence": 0.92
    }
  ]
}
```

---

## Management API

### GET /v1/manage/health
**Purpose**: System health check

**Response** (200 OK):
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "celery_workers": "healthy"
  },
  "metrics": {
    "items_total": 12543,
    "items_processed_today": 87,
    "queue_depth": 3,
    "avg_enrichment_time_ms": 2340
  }
}
```

---

### GET /v1/manage/stats
**Purpose**: System statistics

**Response** (200 OK):
```json
{
  "totals": {
    "content_items": 12543,
    "themes": 47,
    "relationships": 3421
  },
  "classifications": {
    "note": 7234,
    "idea": 2341,
    "reference": 1876,
    "task": 892,
    "meeting_notes": 200
  },
  "activity": {
    "items_last_7_days": 87,
    "items_last_30_days": 412
  }
}
```

---

## Error Responses

All endpoints use consistent error format:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Content is required",
    "details": {
      "field": "content",
      "constraint": "not_empty"
    }
  },
  "request_id": "req_abc123"
}
```

**Error Codes**:
- `INVALID_REQUEST` (400) - Malformed request
- `UNAUTHORIZED` (401) - Missing/invalid API key
- `NOT_FOUND` (404) - Resource doesn't exist
- `RATE_LIMITED` (429) - Too many requests
- `INTERNAL_ERROR` (500) - Server error

---

## Rate Limiting

**Default Limits**:
- Capture: 100 requests/minute
- Retrieval: 300 requests/minute
- Insights: 60 requests/minute

**Headers** (included in all responses):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1705329600
```

---

## OpenAPI Specification

Full OpenAPI 3.0 spec will be generated and available at:
- **Interactive docs**: `/docs` (Swagger UI)
- **Alternative docs**: `/redoc` (ReDoc)
- **JSON spec**: `/openapi.json`

---

**Last Updated**: 2026-01-12
