# 06: Data Flow & Database Architecture

This document explains how browser events enter the system, how they are stored in the database schema, and how relationships link events to sessions, memories, and investigations.

---

## 1. Browser Event Format
Raw events captured by the Chrome extension (`browser-extension/src/background.js`) are serialized as JSON Lines:

```json
{
  "timestamp": "2026-08-20T11:05:12.184Z",
  "url": "https://stackoverflow.com/questions/tagged/spring-boot",
  "pageTitle": "Newest 'spring-boot' Questions - Stack Overflow",
  "event": "page_loaded",
  "input": null,
  "content": "Spring Boot makes it easy to create stand-alone, production-grade Spring based Applications..."
}
```

### Event Type Normalization
Raw logs may contain legacy `"event": "input"` or `"event": "search"`. The sync pipeline (`apps/api/services/sync_log.py`) normalizes these into the standard Pydantic enum `EventType`:
- `page_loaded`
- `input_submitted`
- `search_submitted`
- `click`
- `link_clicked`
- `page_content`
- `navigation`

---

## 2. Database Schema (`models/`)

The application uses SQLAlchemy with dual-dialect support (SQLite for local standalone execution, PostgreSQL with `pgvector` for scalable production deployment).

```
                      +-------------------+
                      |   BrowserSession  |
                      |-------------------|
                      | id (UUID)         |
                      | start_time        |
                      | end_time          |
                      | duration_seconds  |
                      | event_count       |
                      +-------------------+
                                │ 1
                                │
                                │ N
                      +-------------------+
                      |       Event       |
                      |-------------------|
                      | id (Integer PK)   |
                      | event_id (UUID)   |<────────┐
                      | session_id (FK)   |         │
                      | timestamp         |         │
                      | event_type        |         │
                      | url, domain       |         │
                      | page_title        |         │
                      | input_text        |         │
                      | content           |         │
                      | metadata_ (JSON)  |         │
                      +-------------------+         │
                                │                   │
                                │                   │
        ┌───────────────────────┴──────────────┐    │
        │                                      │    │
        v                                      v    │
+-------------------+                  +--------------------+
|  Investigation    |                  |   MemoryEvidence   |
|-------------------|                  |--------------------|
| id (UUID)         |                  | memory_id (UUID FK)|
| query             |                  | event_id (UUID FK)─┘
| status            |                  +--------------------+
| summary           |                            ▲
| plan (JSON)       |                            │
+-------------------+                  +--------------------+
        │ 1                            |       Memory       |
        │                              |--------------------|
        │ N                            | id (UUID)          |
+---------------------+                | type (FACT/PREF)   |
| InvestigationAction |                | content            |
|---------------------|                | embedding (384-d)  |
| id (UUID)           |                +--------------------+
| investigation_id(FK)|
| action_type         |
| input_data (JSON)   |
| output_data (JSON)  |
+---------------------+
```

### Key Tables Explained

#### `Event` (`models/events.py`)
- `id`: Integer auto-incrementing primary key.
- `event_id`: Unique UUIDv4 used for evidence citations and external MCP references.
- `session_id`: Foreign key pointing to `BrowserSession.id`.
- `timestamp`: UTC datetime of the interaction.
- `event_type`: Categorized enum (`page_loaded`, `input_submitted`, `click`, etc.).
- `url`, `domain`: Extracted web address and host domain (e.g. `stackoverflow.com`).
- `page_title`, `input_text`, `content`: Text fields used for keyword and dense vector indexing.

#### `BrowserSession` (`models/sessions.py`)
- Represents a continuous block of activity separated by $\ge 30$ minutes of inactivity.
- Fields: `start_time`, `end_time`, `duration_seconds`, `event_count`, `active_domains` (JSON map).

#### `Memory` & `MemoryEvidence` (`models/memories.py`)
- `Memory`: Stores atomic extracted facts (e.g. *"User searched Spring Boot batch insert optimization on stackoverflow.com"*), type (`FACT`, `PREFERENCE`, `LONG_TERM_INTEREST`), and 384-dimensional vector embedding.
- `MemoryEvidence`: Junction table linking a memory to the exact raw `Event.event_id` records that proved it.

#### `Investigation` & `InvestigationAction` (`models/investigations.py`)
- Audit log of every natural language query processed.
- `plan`: JSON object recording which routes fired and candidate counts.
- `InvestigationAction`: Records individual intermediate retrieval steps and tool invocations.

---

## 3. End-to-End Event Lifecycle

1. **Capture**: Browser extension injects content scripts and event listeners.
2. **Ingestion**: Event posted to `/api/v1/events` or synced from `events.log`.
3. **PII Sanitization**: `utils/privacy.py` redacts email patterns, credit card patterns, and bearer tokens.
4. **Session Assignment**: `assign_unassigned_events_to_sessions` evaluates timestamps and links `Event.session_id`.
5. **Memory Extraction**: `extract_memories_from_session` indexes key search events into `Memory` vectors.
6. **Query & Retrieval**: When queried, events are retrieved, fused via RRF, reranked, and cited in the final answer.
