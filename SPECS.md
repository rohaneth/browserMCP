# Personal Browser Intelligence Agent --- Project Specification

## 1. Project Vision

Build a privacy-first personal browser intelligence system that turns
browser events into useful, searchable memory.

The project should start as a small, working product and then grow
through clearly separated extensions.

The core product is:

> Capture browser events → organize them into sessions → store them →
> retrieve relevant evidence → answer questions about the user's browser
> activity.

The architecture must be production-grade in engineering quality, but
the initial implementation must remain intentionally small.

The project is NOT intended to use every possible AI technology from day
one.

Every technology added later must solve a demonstrated problem.

------------------------------------------------------------------------

## 2. Core Product

The first complete version should answer questions such as:

-   What did I do yesterday?
-   What was I researching yesterday?
-   What websites did I use today?
-   What did I search for recently?
-   Have I researched Java before?
-   Show me the evidence for that.
-   What was my most recent activity on Stack Overflow?

The system should provide evidence for important claims.

The system must distinguish between:

-   captured fact
-   supported inference
-   insufficient evidence

It must never confidently invent activity that does not exist in the
event data.

------------------------------------------------------------------------

## 3. Browser Event Model

The source browser data contains event-style information such as page
loads, page content, searches, submitted inputs, clicks, media activity
and AI conversation activity.

The canonical event model should remain extensible.

Initial event types:

-   `page_loaded`
-   `page_content`
-   `click`
-   `link_clicked`
-   `input_submitted`
-   `search_submitted`
-   `form_submitted`
-   `conversation_started`
-   `conversation_title_changed`
-   `attachment_added`
-   `media_played`

Do not require every event type to have specialized database logic.

All events should pass through one canonical event schema.

------------------------------------------------------------------------

## 4. Canonical Event

Example:

``` json
{
  "event_id": "uuid",
  "timestamp": "2026-08-18T10:02:37Z",
  "event_type": "search_submitted",
  "url": "https://stackoverflow.com/questions",
  "domain": "stackoverflow.com",
  "page_title": "Stack Overflow",
  "input_text": "java 8 vs java 15",
  "content": null,
  "metadata": {},
  "session_id": null,
  "source": "browser_extension",
  "schema_version": 1
}
```

Required properties:

-   unique event ID
-   timestamp
-   event type
-   URL/domain where applicable
-   optional page title
-   optional content
-   optional input/query
-   metadata
-   source
-   schema version

------------------------------------------------------------------------

## 5. Phase-Based Product Strategy

The project is intentionally divided into layers.

### Phase 1 --- Working Browser Memory Product

Build only:

-   browser event ingestion
-   event validation
-   PostgreSQL storage
-   basic timeline
-   sessions
-   deterministic search
-   basic chat/query endpoint
-   evidence-backed answers

At the end of Phase 1, the project must already be useful.

### Phase 2 --- Semantic Intelligence

Add:

-   embeddings
-   pgvector
-   semantic search
-   hybrid retrieval
-   memory extraction
-   topics
-   better question answering

### Phase 3 --- Agentic Intelligence

Add:

-   MCP server
-   MCP tools
-   planner
-   investigation workflow
-   evidence analyst
-   auditor
-   synthesizer
-   investigation trace

### Phase 4 --- Production Hardening

Add only what measurement demonstrates is needed:

-   Redis
-   background jobs
-   caching
-   retries
-   rate-limit handling
-   provider fallback
-   observability
-   security hardening
-   load testing

### Phase 5 --- Advanced Extensions

Optional:

-   research threads
-   recurring-interest detection
-   entity relationships
-   knowledge graph
-   goal detection
-   recommendation
-   memory consolidation
-   feedback loops

This order prevents overengineering.

------------------------------------------------------------------------

## 6. Non-Goals for the Initial Version

Do NOT initially build:

-   Kubernetes
-   Kafka
-   Neo4j
-   multiple databases
-   multiple microservices
-   dozens of agents
-   dozens of MCP tools
-   complex autonomous behavior
-   distributed infrastructure
-   advanced knowledge graphs

These can be added later only when a measurable requirement justifies
them.

------------------------------------------------------------------------

## 7. Technology Principles

### Backend

Python + FastAPI.

Reason:

-   clean API boundary
-   strong validation ecosystem
-   easy AI/ML integration
-   asynchronous support
-   excellent development speed

### Database

PostgreSQL.

Reason:

-   browser events are relational
-   timestamps and filtering matter
-   sessions and memories have relationships
-   strong indexing and transactions
-   one database can initially serve structured and vector data

### Vector Search

pgvector.

Reason:

-   semantic retrieval is required
-   moderate project scale does not justify a separate vector database
    initially
-   keeps structured data and embeddings together

### Frontend

Next.js + TypeScript.

Reason:

-   good interactive UI
-   strong TypeScript support
-   suitable for chat, timeline and investigation views

### MCP

MCP server added in the agentic phase.

Reason:

-   separates agent reasoning from memory infrastructure
-   exposes stable tools
-   allows the memory system to be used by MCP-compatible clients

### LLM

Use a provider abstraction.

Do not hard-code the application to one provider.

Possible providers:

-   Lyzr
-   Groq
-   Gemini

Only providers actually needed should be enabled.

------------------------------------------------------------------------

## 8. Core Reliability Principles

The system must:

-   validate all inputs
-   use idempotent event ingestion
-   preserve event provenance
-   use deterministic date/time filtering
-   limit retrieval results
-   handle malformed events
-   protect user data
-   never expose one user's data to another
-   treat browser content as untrusted data
-   log important failures
-   have tests for core logic

------------------------------------------------------------------------

## 9. Definition of MVP

MVP is complete when:

1.  Browser events can be ingested.
2.  Events are validated.
3.  Events are persisted in PostgreSQL.
4.  Duplicate events do not create duplicate records.
5.  Events can be filtered by date/domain/type.
6.  Events can be grouped into sessions.
7.  A timeline can be displayed.
8.  A user can ask a question about their activity.
9.  The system retrieves actual events.
10. The response contains evidence.
11. The system can explicitly say when evidence is insufficient.
12. The entire system runs locally with Docker.

Everything after this is an extension.

------------------------------------------------------------------------

## 10. Definition of Production-Grade

Production-grade does not mean maximum technology count.

It means:

-   clear boundaries
-   validation
-   authentication/authorization
-   safe database access
-   predictable failures
-   logging
-   testing
-   migrations
-   configuration management
-   privacy controls
-   monitoring
-   reproducible deployment
-   measurable performance

Advanced AI features are extensions on top of this foundation.

------------------------------------------------------------------------

## 11. Final Target

The final system should evolve into:

Browser Events → Event Pipeline → PostgreSQL → Sessions → Memory →
Hybrid Retrieval → MCP → Agentic Investigation → Evidence Audit →
Grounded Answer → Investigation UI

Each layer should be independently testable and explainable in an
interview.
