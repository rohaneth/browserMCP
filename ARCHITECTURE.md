# Personal Browser Intelligence Agent --- Architecture

## 1. Architectural Philosophy

The architecture is intentionally incremental.

The first version is a modular monolith.

Do not start with microservices.

The system should evolve as:

``` text
Phase 1

Browser
  ↓
FastAPI
  ↓
PostgreSQL
  ↓
Query Service
  ↓
Next.js
```

Then:

``` text
Phase 2

Browser
  ↓
FastAPI
  ↓
PostgreSQL + pgvector
  ↓
Retrieval
  ↓
LLM
  ↓
Next.js
```

Then:

``` text
Phase 3

Browser
  ↓
FastAPI
  ↓
Memory/Retrieval
  ↓
MCP Server
  ↓
Agent
  ↓
Auditor
  ↓
Next.js
```

Then production hardening is added only where required.

------------------------------------------------------------------------

## 2. System Context

``` text
+-------------------+
| Browser Extension |
+---------+---------+
          |
          | HTTPS
          v
+-------------------+
|     FastAPI       |
|  Ingestion API   |
+---------+---------+
          |
          v
+-------------------+
|    PostgreSQL     |
| Events / Sessions |
| Memories / Users  |
+---------+---------+
          |
          v
+-------------------+
| Query/Retrieval   |
| Service           |
+---------+---------+
          |
          v
+-------------------+
|      Next.js      |
| Chat + Timeline   |
+-------------------+
```

------------------------------------------------------------------------

## 3. Phase 1 Architecture

### Browser Extension

Responsibilities:

-   observe supported browser events
-   normalize basic client information
-   batch events when appropriate
-   send events to the API
-   retry transient network failures

It must not contain database credentials.

### FastAPI

Responsibilities:

-   authentication
-   request validation
-   event validation
-   idempotency
-   authorization
-   database writes
-   query endpoints
-   health checks

### PostgreSQL

Initial tables:

``` text
users
events
sessions
```

Later tables are added through migrations.

### Query Service

Initially deterministic.

It handles:

-   date filtering
-   domain filtering
-   event type filtering
-   keyword search
-   chronological ordering
-   session lookup

Do not use an LLM for deterministic filtering.

------------------------------------------------------------------------

## 4. Phase 2 Architecture

Add:

``` text
+-------------------+
| Memory Processor  |
+---------+---------+
          |
          +------> Memory Extraction
          |
          +------> Topic Extraction
          |
          +------> Embeddings
                         |
                         v
                    pgvector
```

The retrieval layer becomes:

``` text
                  Query
                    |
          +---------+---------+
          |         |         |
          v         v         v
       Keyword   Vector   Metadata
          |         |         |
          +---------+---------+
                    |
                    v
               Fusion/Rank
                    |
                    v
                 Evidence
```

------------------------------------------------------------------------

## 5. Phase 3 Architecture

The agent should not directly know PostgreSQL internals.

``` text
+-------------+
|    Agent    |
+------+------+
       |
       | MCP
       v
+-------------+
| MCP Server  |
+------+------+
       |
       v
+----------------------+
| Memory Tool Layer    |
+----------+-----------+
           |
           v
+----------------------+
| Retrieval Services   |
+----------+-----------+
           |
           v
+----------------------+
| PostgreSQL/pgvector  |
+----------------------+
```

This creates a clean separation:

Agent reasoning ≠ database implementation.

------------------------------------------------------------------------

## 6. Agent Workflow

Use a single investigation graph initially.

``` text
User Query
   |
   v
Planner
   |
   v
Retriever
   |
   v
Analyst
   |
   v
Auditor
   |
   v
Synthesizer
   |
   v
Answer
```

Not every query needs every stage.

For example:

``` text
"What did I do yesterday?"

Planner
  ↓
Deterministic retrieval
  ↓
Simple synthesis
```

A complex question may use:

``` text
Planner
  ↓
Multiple MCP calls
  ↓
Hybrid retrieval
  ↓
Analyst
  ↓
Auditor
  ↓
Synthesizer
```

------------------------------------------------------------------------

## 7. MCP Tools

Start with only:

``` text
search_events
search_memory
get_timeline
get_session
get_activity
get_evidence
```

Add tools only when an agent task requires them.

Every tool must define:

-   input schema
-   output schema
-   authorization rules
-   maximum result size
-   timeout
-   error behavior

------------------------------------------------------------------------

## 8. Evidence Model

The most important architectural rule is:

``` text
Claim → Evidence → Original Event
```

Example:

``` text
Claim:
User researched Java versions.

Evidence:
Search query "java 8 vs java 15".

Original Event:
event_123
```

The final answer should be able to navigate back to the original event.

------------------------------------------------------------------------

## 9. Fact vs Inference

Store claims explicitly.

``` text
Claim
-----
type:
  FACT
  INFERENCE
  UNCERTAIN

confidence
evidence_ids
```

Example:

``` text
FACT:
The user searched for "java 8 vs java 15".

INFERENCE:
The user was probably comparing Java versions.

UNSUPPORTED:
The user decided to upgrade to Java 15.
```

The final claim must not exceed what its evidence supports.

------------------------------------------------------------------------

## 10. Privacy Boundary

``` text
Browser
  ↓
Raw Event
  ↓
Privacy Filter
  ↓
Validated Event
  ↓
Storage
```

External LLM:

``` text
Stored Evidence
  ↓
Minimum Necessary Context
  ↓
LLM
```

Never send the entire browser history to an LLM for a simple question.

------------------------------------------------------------------------

## 11. Untrusted Browser Content

All browser page content must be treated as untrusted.

``` text
Web Page
  ↓
Captured Text
  ↓
UNTRUSTED DATA
  ↓
Evidence
```

It must never override system/agent instructions.

This protects against prompt injection embedded in webpages.

------------------------------------------------------------------------

## 12. Database Evolution

Initial:

``` text
users
events
sessions
```

Phase 2:

``` text
memories
memory_evidence
embeddings
topics
entities
```

Phase 3:

``` text
investigations
agent_steps
tool_calls
audit_results
```

Do not create tables before the feature that requires them exists.

------------------------------------------------------------------------

## 13. Recommended Project Structure

``` text
browser-intelligence-agent/
├── apps/
│   ├── api/
│   ├── worker/
│   ├── mcp/
│   └── web/
├── packages/
│   ├── domain/
│   ├── ingestion/
│   ├── memory/
│   ├── retrieval/
│   ├── agents/
│   ├── llm/
│   └── privacy/
├── browser-extension/
├── database/
│   └── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── evals/
├── docs/
├── docker-compose.yml
├── .env.example
├── README.md
├── SPECS.md
├── ARCHITECTURE.md
└── TASKS.md
```

------------------------------------------------------------------------

## 14. Why Modular Monolith First?

A modular monolith gives:

-   simpler development
-   easier debugging
-   fewer deployment problems
-   easier local testing
-   clear module boundaries

It can later be split into services if measurements justify it.

Interview answer:

> "I deliberately started with a modular monolith because the system
> didn't initially have enough scale to justify distributed services.
> The internal boundaries allow individual components to be extracted
> later."

------------------------------------------------------------------------

## 15. When to Add Redis

Do not add Redis initially unless needed.

Add it if:

-   repeated queries are expensive
-   cache hit rate is measurable
-   background task coordination needs it
-   rate limiting needs shared state

Measure before and after.

------------------------------------------------------------------------

## 16. When to Add a Queue

Add a queue when:

-   event volume increases
-   embeddings slow ingestion
-   memory extraction becomes expensive
-   jobs need retry semantics

Until then, a simple background worker is enough.

------------------------------------------------------------------------

## 17. When to Add a Dedicated Vector Database

Do not start with one.

Use pgvector first.

Consider a dedicated vector database only if:

-   vector scale becomes large
-   retrieval performance requires it
-   operational requirements justify another system

The project should demonstrate that the decision came from requirements
rather than fashion.

------------------------------------------------------------------------

## 18. When to Add a Knowledge Graph

Only add one if relationship queries become important.

Example:

``` text
Java
 ├── related to → Spring Boot
 ├── researched on → Stack Overflow
 └── appeared in → Project X
```

Until then, PostgreSQL relationships are sufficient.

------------------------------------------------------------------------

## 19. Observability Evolution

Phase 1:

-   structured logs
-   request IDs
-   error logging

Phase 2:

-   latency metrics
-   LLM usage

Phase 3:

-   OpenTelemetry
-   agent traces
-   MCP traces
-   retrieval traces

This prevents observability from becoming unnecessary complexity too
early.

------------------------------------------------------------------------

## 20. Deployment

Local development:

``` text
Docker Compose
 ├── PostgreSQL
 ├── API
 ├── Worker
 ├── MCP
 └── Web
```

Production can initially use the same logical components.

Do not introduce Kubernetes unless deployment scale actually requires
it.

------------------------------------------------------------------------

## 21. Production Architecture Target

``` text
                     Browser
                        |
                        v
                 +-------------+
                 | API Gateway |
                 +------+------+
                        |
                 +------+------+
                 |   FastAPI   |
                 +------+------+
                        |
            +-----------+-----------+
            |                       |
            v                       v
      PostgreSQL                 Worker
      + pgvector                   |
            |                      |
            |              +-------+-------+
            |              |       |       |
            |              v       v       v
            |           Memory  Embed  Topics
            |
            v
       Retrieval
            |
            v
        MCP Server
            |
            v
       Agent Graph
            |
       +----+----+
       |         |
       v         v
    Auditor  Synthesizer
       |         |
       +----+----+
            |
            v
          Web UI
```

This is the target, not the starting point.

------------------------------------------------------------------------

## 22. Data Ingestion Limits & Validation

To protect the ingestion boundary from memory exhaustion and abusive payloads, explicit limits are enforced on incoming browser events:

| Field | Limit | Reason | Enforcement Layer |
|-------|-------|--------|-------------------|
| `url` / `canonical_url` | 2048 chars | Standard maximum URL length supported by browsers. | Pydantic Schema |
| `domain` | 255 chars | Standard DNS maximum length. | Pydantic Schema |
| `page_title` | 1000 chars | Ample space for titles; prevents unbounded string abuse. | Pydantic Schema |
| `content` | 100,000 chars | Preserves sufficient web page content for future LLM semantic memory extraction without unbounded memory consumption (~100KB per event). | Pydantic Schema |
| `input_text` | 10,000 chars | Covers extensive user input while blocking massive paste bombs. | Pydantic Schema |
| `metadata` | Depth: 5, Keys: 100, Size: 10KB | Prevents deeply nested objects and massive JSON payloads from locking up the JSONB parser or memory. | Pydantic Schema Validator |
| `batch size` | 500 events | Balances network efficiency with transaction size and memory consumption. | Pydantic Schema Validator |

### Interview Explanations

**Why reject oversized events instead of silently truncating them?**
> "Silent truncation fundamentally alters the meaning of browser history. If we truncate a 200,000-character article to 50,000 characters, the LLM will hallucinate or miss critical context downstream when trying to reason about the event, assuming it read the whole article. Rejecting oversized payloads explicitly with HTTP 422 maintains data integrity and makes it clear to the client (extension) that the event cannot be processed, rather than polluting our data warehouse with incomplete facts."

**Why are content limits enforced at the API boundary?**
> "The API boundary is our zero-trust entry point. If we wait to enforce limits at the database layer (e.g., using `VARCHAR(10000)` instead of `TEXT`), the API server still has to deserialize and hold the massive JSON payload in memory, opening us up to OOM (Out of Memory) crashes. Pydantic drops the payload immediately during schema validation before it reaches our business logic or database."

------------------------------------------------------------------------

## 23. Server-Side Privacy Boundary

### Threat Model & Defense Strategy
The browser extension already performs client-side privacy filtering to prevent secrets from leaving the browser. However, **the browser is not a trusted security boundary**. A malicious actor could modify the extension, or a compromised browser could bypass client-side checks and send raw payloads directly to the API.

To protect the system, we implement a **Server-Side Defense-in-Depth Privacy Boundary**. 

### Detection and Redaction Strategy
We use deterministic, high-confidence regular expressions (heuristics) targeting obvious secrets (e.g., `password=...`, Bearer tokens, private keys, credit cards). 
- **Redaction over Deletion**: Rather than dropping the entire event (which breaks deduplication and destroys legitimate surrounding context), we redact the matched value inline (e.g., `password=[REDACTED]`).
- **False-Positive Tradeoff**: Perfect DLP is intentionally out of scope. We prioritize **High Precision > High Recall**. Overly aggressive filtering (e.g., matching the word "account") would destroy legitimate semantic memory.
- **Why Heuristics over LLMs?**: Deterministic rules are synchronous, ultra-fast, cheap, and predictable. Sending potential secrets to an external LLM for classification introduces severe latency and creates a massive new privacy vulnerability (leaking secrets to a third-party LLM).

### Interview Explanation

**Why do you filter sensitive data on the server if the browser extension already filters it?**
> "The browser is an untrusted environment. If we rely purely on client-side filtering, anyone who modifies the extension or interacts directly with the API could inject sensitive secrets into our database, turning our application into a toxic data store. The server must independently verify and protect its persistent storage."

**Why didn't you use an LLM for sensitive-data detection?**
> "Deterministic high-confidence rules are faster, cheaper, predictable, and auditable. More importantly, using an LLM to detect secrets means we are actively transmitting suspected plaintext passwords and API keys to a third-party AI provider, which fundamentally violates the core privacy goals of the system."

------------------------------------------------------------------------

## 24. User Privacy Controls

### Architecture & Philosophy
Users must have absolute control over their browser memory. We implement a persistent settings system that can suspend event ingestion and delete existing events. This logic resides in a centralized `CollectionSettings` database singleton.

### Features
1. **Pause/Resume Collection**: `POST /api/v1/privacy/pause` and `POST /api/v1/privacy/resume`. Modifies the `is_paused` setting. When paused, the `create_event` and `create_events_batch` routes preemptively reject events with a 403 Forbidden ("paused" status). This guarantees no events are saved, without silently dropping them (silent drops can lead to client confusion).
2. **Delete Single Event**: `DELETE /api/v1/privacy/events/{event_id}`. Deletes a specific event. Uses Postgres `ON DELETE CASCADE` through the `MemoryEvidence` junction table to automatically and safely sever the provenance link from derived semantic memories.
3. **Delete Date Range**: `DELETE /api/v1/privacy/events?start_time=X&end_time=Y`. Allows sweeping cleanup. Boundary convention is strictly `[start_time, end_time)`. This is a single, atomic bulk-delete transaction.

### Security Tradeoffs
- **No LLM / Kafka / Redis**: Pause state is managed via Postgres settings rows and endpoints execute transactions directly. Introducing Redis for settings cache or Kafka for event streams would exponentially increase architectural complexity and break the "Modular Monolith First" philosophy.
- **Why Server-Side?**: Client-side pausing isn't enough. An attacker or a malfunctioning browser extension could ignore the client-side pause state and continue sending events. Server-side validation guarantees the database is fully protected during a pause.
