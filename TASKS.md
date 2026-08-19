# Personal Browser Intelligence Agent --- TASKS

## How to Use This File

Complete tasks strictly in order.

Do not jump to advanced AI features before the foundation works.

After every phase:

1.  Run tests.
2.  Run the application.
3.  Verify the acceptance criteria.
4.  Commit the working version.
5.  Update the README.
6.  Record important architectural decisions.

A phase is complete only when its acceptance criteria pass.

------------------------------------------------------------------------

# PHASE 0 --- Project Foundation

## Task 0.1 --- Create Repository

Create the repository structure.

Deliver:

``` text
apps/
packages/
browser-extension/
database/
tests/
evals/
docs/
```

Acceptance:

-   repository starts cleanly
-   README exists
-   SPECS.md exists
-   ARCHITECTURE.md exists
-   TASKS.md exists

------------------------------------------------------------------------

## Task 0.2 --- Establish Development Environment

Set up:

-   Python
-   Node.js
-   PostgreSQL
-   Docker
-   environment variables

Create:

``` text
.env.example
```

Never commit real secrets.

------------------------------------------------------------------------

## Task 0.3 --- Docker Compose

Create a minimal Compose setup.

Initially:

``` text
PostgreSQL
API
Web
```

Do not add Redis, queues or other infrastructure yet.

Acceptance:

``` text
docker compose up
```

starts the system.

------------------------------------------------------------------------

## Task 0.4 --- Code Quality

Set up:

Python:

-   Ruff
-   Black
-   Pytest

TypeScript:

-   ESLint
-   Prettier
-   TypeScript

Acceptance:

CI can run linting and tests.

------------------------------------------------------------------------

# PHASE 1 --- Browser Event Ingestion

## Task 1.1 --- Define Event Schema

Implement the canonical browser event model.

Use Pydantic.

Support:

-   event ID
-   timestamp
-   event type
-   URL
-   domain
-   title
-   content
-   input text
-   metadata
-   source
-   schema version

Write unit tests.

------------------------------------------------------------------------

## Task 1.2 --- Create Events Table

Create PostgreSQL migration.

Include:

``` text
id
event_id
timestamp
event_type
url
canonical_url
domain
page_title
content
input_text
metadata
source
schema_version
created_at
```

Add indexes for:

-   event_id
-   timestamp
-   domain
-   event_type

------------------------------------------------------------------------

## Task 1.3 --- Implement POST /events

Implement:

``` text
POST /api/v1/events
```

Requirements:

-   validation
-   authentication boundary
-   idempotency
-   database transaction
-   structured errors

------------------------------------------------------------------------

## Task 1.4 --- Batch Ingestion

Implement:

``` text
POST /api/v1/events/batch
```

The endpoint must safely process multiple events.

Test:

-   valid batch
-   partially invalid batch
-   duplicate batch
-   empty batch
-   oversized batch

------------------------------------------------------------------------

## Task 1.5 --- Event Deduplication

Implement duplicate detection using:

``` text
event_id
```

Optionally detect near-duplicates later.

Acceptance:

Submitting the same event twice results in one stored event.

------------------------------------------------------------------------

## Task 1.6 --- Browser Extension Skeleton

Create the extension.

Implement minimal event capture.

Do NOT attempt every event type immediately.

Start with:

``` text
page_loaded
search_submitted
click
```

------------------------------------------------------------------------

## Task 1.7 --- Connect Browser to API

Browser extension sends events to FastAPI.

Test:

``` text
Browser
→ API
→ PostgreSQL
```

Acceptance:

A real browser action produces a database record.

------------------------------------------------------------------------

## Task 1.8 --- Phase 1 Checkpoint

Verify:

-   events arrive
-   events are validated
-   duplicates are rejected
-   events persist
-   browser works
-   Docker works
-   tests pass

Commit:

``` text
phase-1-event-ingestion
```

------------------------------------------------------------------------

# PHASE 2 --- Semantic Storage & Event Normalization

## Task 2.1 --- Database Vector Store (COMPLETED)

Establish the semantic-memory storage foundation using PostgreSQL + `pgvector`.
(This fulfills the foundational parts of Phase 5, implemented early).

- Created `memories` table with `VECTOR(384)`.
- Created `memory_evidence` table for provenance.
- Implemented Alembic migrations.

------------------------------------------------------------------------

## Task 2.2 --- URL & Domain Normalization

Implement canonical URL and Domain normalization.
Remove irrelevant tracking parameters where safe.
Normalize domains (e.g., `www.example.com` to `example.com`).

Write tests.

------------------------------------------------------------------------

## Task 2.3 --- Event Content Limits

Prevent oversized payloads.

Define maximum sizes for:

-   URL
-   title
-   input
-   content
-   metadata

------------------------------------------------------------------------

## Task 2.4 --- Basic Sensitive Data Filtering

Implement an initial privacy layer.

At minimum detect:

-   email addresses
-   obvious API keys/tokens
-   sensitive URLs

Do not claim perfect PII detection.

------------------------------------------------------------------------

## Task 2.5 --- User Privacy Controls

Implement:

``` text
pause collection
resume collection
delete event
delete date range
```

------------------------------------------------------------------------

## Task 2.6 --- Privacy Tests

Test:

-   PII
-   secrets
-   excluded domains
-   oversized content
-   malicious input

------------------------------------------------------------------------

## Task 2.7 --- Phase 2 Checkpoint

Acceptance:

Vector foundation is active. A privacy-filtered event can travel from browser to database without leaking configured sensitive values.

Commit:

``` text
phase-2-storage-and-privacy
```

------------------------------------------------------------------------

# PHASE 3 --- Sessions and Timeline

## Task 3.1 --- Sessions Table

Create:

``` text
sessions
```

Fields:

``` text
id
user_id
start_time
end_time
event_count
created_at
updated_at
```

------------------------------------------------------------------------

## Task 3.2 --- Sessionization Algorithm

Start with deterministic time-gap sessionization.

Default:

``` text
30 minutes
```

Make it configurable.

------------------------------------------------------------------------

## Task 3.3 --- Assign Events to Sessions

Process events chronologically.

Create or reuse sessions.

Acceptance:

Related events are grouped correctly.

------------------------------------------------------------------------

## Task 3.4 --- Timeline API

Implement:

``` text
GET /api/v1/timeline
```

Support:

-   start time
-   end time
-   domain
-   event type

------------------------------------------------------------------------

## Task 3.5 --- Timeline UI

Create a timeline showing:

-   time
-   domain
-   title
-   event type
-   query/input where available

------------------------------------------------------------------------

## Task 3.6 --- Phase 3 Checkpoint

The application should now answer:

> "What did I do yesterday?"

without an LLM.

Commit:

``` text
phase-3-sessions-timeline
```

------------------------------------------------------------------------

# PHASE 4 --- Deterministic Search

## Task 4.1 --- Event Search API

Implement:

``` text
GET /api/v1/events/search
```

Support:

-   keyword
-   date
-   domain
-   event type

------------------------------------------------------------------------

## Task 4.2 --- PostgreSQL Full Text Search

Add PostgreSQL full-text search.

Do not introduce Elasticsearch.

------------------------------------------------------------------------

## Task 4.3 --- Temporal Query Parsing

Support deterministic expressions:

-   today
-   yesterday
-   last week
-   date ranges

Use code, not an LLM.

------------------------------------------------------------------------

## Task 4.4 --- Evidence Objects

Create a common evidence structure:

``` text
event_id
timestamp
url
title
snippet
relevance
```

------------------------------------------------------------------------

## Task 4.5 --- Basic Question Answering

Implement:

``` text
POST /api/v1/query
```

Flow:

``` text
Question
→ Query parser
→ Retrieval
→ Evidence
→ Answer
```

At this point the answer may use a simple LLM.

------------------------------------------------------------------------

## Task 4.6 --- Insufficient Evidence Handling

If retrieval finds nothing:

Return:

> I could not find sufficient evidence in the captured browser activity.

Never fabricate an answer.

------------------------------------------------------------------------

## Task 4.7 --- Phase 4 Checkpoint

The system should now be a usable product.

It should answer questions using actual captured evidence.

Commit:

``` text
phase-4-search-and-qa
```

------------------------------------------------------------------------

# PHASE 5 --- Semantic Memory

This is the first major Applied AI extension.

## Task 5.1 --- Introduce Memory Model (FULFILLED BY TASK 2.1)

The vector storage foundation, `memories`, and `memory_evidence` tables have already been implemented in Phase 2.
Skip table creation here.

------------------------------------------------------------------------

## Task 5.2 --- Memory Extraction

Given a session, extract meaningful memories.

Example:

Events:

``` text
search Java 8 vs Java 15
open Stack Overflow
read Java compatibility discussion
```

Memory:

``` text
User investigated Java version differences.
```

Store evidence IDs.

------------------------------------------------------------------------

## Task 5.3 --- Embedding Pipeline

Choose one embedding model.

Do not add multiple embedding providers yet.

Generate embeddings for:

-   meaningful memories
-   selected content chunks
-   session summaries

------------------------------------------------------------------------

## Task 5.4 --- pgvector

Add pgvector to PostgreSQL.

Create vector indexes when justified by dataset size.

------------------------------------------------------------------------

## Task 5.5 --- Semantic Search

Implement:

``` text
search_similar_memories(query)
```

------------------------------------------------------------------------

## Task 5.6 --- Compare Keyword vs Vector

Build a small evaluation set.

Measure:

-   Recall@K
-   MRR

Record failures.

------------------------------------------------------------------------

## Task 5.7 --- Phase 5 Checkpoint

The system can answer semantic questions such as:

> "Have I researched Java versions before?"

Commit:

``` text
phase-5-semantic-memory
```

------------------------------------------------------------------------

# PHASE 6 --- Hybrid Retrieval

## Task 6.1 --- Combine Keyword and Vector Search

Implement:

``` text
keyword score
+
vector score
+
metadata filters
```

------------------------------------------------------------------------

## Task 6.2 --- Temporal Filtering

Ensure queries like:

> "What did I research yesterday about Java?"

apply date filtering before or alongside semantic retrieval.

------------------------------------------------------------------------

## Task 6.3 --- Ranking

Implement a simple fusion/ranking algorithm.

Do not introduce a complicated reranker immediately.

------------------------------------------------------------------------

## Task 6.4 --- Evaluation

Compare:

``` text
keyword
vector
hybrid
```

Use the same benchmark.

------------------------------------------------------------------------

## Task 6.5 --- Decide Whether Reranking Is Needed

Only add a reranker if the benchmark demonstrates that retrieval quality
needs it.

If added:

-   document why
-   benchmark before/after
-   record latency impact

------------------------------------------------------------------------

## Task 6.6 --- Phase 6 Checkpoint

Hybrid retrieval must outperform or provide a clear tradeoff against the
previous approaches.

Commit:

``` text
phase-6-hybrid-retrieval
```

------------------------------------------------------------------------

# PHASE 7 --- MCP Server

## Task 7.1 --- Create MCP Server

Create the MCP application.

Do not expose database internals.

------------------------------------------------------------------------

## Task 7.2 --- Implement First MCP Tool

``` text
search_events
```

------------------------------------------------------------------------

## Task 7.3 --- Add Timeline Tool

``` text
get_timeline
```

------------------------------------------------------------------------

## Task 7.4 --- Add Memory Search

``` text
search_memory
```

------------------------------------------------------------------------

## Task 7.5 --- Add Session Tool

``` text
get_session
```

------------------------------------------------------------------------

## Task 7.6 --- Add Activity Tool

``` text
get_activity
```

------------------------------------------------------------------------

## Task 7.7 --- Add Evidence Tool

``` text
get_evidence
```

------------------------------------------------------------------------

## Task 7.8 --- MCP Authorization

Every MCP call must be scoped to the authenticated user.

------------------------------------------------------------------------

## Task 7.9 --- MCP Testing

Test:

-   valid calls
-   invalid inputs
-   authorization
-   result limits
-   timeouts
-   failures

------------------------------------------------------------------------

## Task 7.10 --- Phase 7 Checkpoint

A client/agent can investigate browser memory entirely through MCP
tools.

Commit:

``` text
phase-7-mcp
```

------------------------------------------------------------------------

# PHASE 8 --- Agentic Investigation

## Task 8.1 --- Create Investigation State

Store:

``` text
investigation_id
query
status
created_at
completed_at
```

------------------------------------------------------------------------

## Task 8.2 --- Planner

The planner decides:

-   what information is needed
-   which tools are appropriate
-   whether the question is simple or complex

------------------------------------------------------------------------

## Task 8.3 --- Retriever

The retriever calls MCP tools.

Keep tool selection constrained.

------------------------------------------------------------------------

## Task 8.4 --- Analyst

Convert evidence into claims.

Every claim must reference evidence.

------------------------------------------------------------------------

## Task 8.5 --- Auditor

Check:

-   evidence support
-   contradictions
-   temporal correctness
-   unsupported inference
-   missing evidence

------------------------------------------------------------------------

## Task 8.6 --- Synthesizer

Generate the final answer from audited claims.

------------------------------------------------------------------------

## Task 8.7 --- Investigation Trace

Store and display:

``` text
planner
tool calls
retrieval
claims
audit
final answer
```

------------------------------------------------------------------------

## Task 8.8 --- Prompt Injection Defense

Treat all browser content as untrusted.

Test with malicious webpage content.

------------------------------------------------------------------------

## Task 8.9 --- Phase 8 Checkpoint

A complex question should produce:

``` text
Question
→ Plan
→ MCP calls
→ Evidence
→ Claims
→ Audit
→ Answer
```

Commit:

``` text
phase-8-agentic-investigation
```

------------------------------------------------------------------------

# PHASE 9 --- Evaluation

## Task 9.1 --- Create Benchmark Dataset

Create at least 50 realistic questions.

Include:

-   temporal questions
-   domain questions
-   semantic questions
-   exact search questions
-   repeated-interest questions
-   insufficient-evidence questions

------------------------------------------------------------------------

## Task 9.2 --- Golden Evidence

For every benchmark question, define expected evidence.

------------------------------------------------------------------------

## Task 9.3 --- Retrieval Metrics

Measure:

-   Recall@5
-   Recall@10
-   MRR

------------------------------------------------------------------------

## Task 9.4 --- Grounding Metrics

Measure:

-   evidence coverage
-   citation accuracy
-   unsupported claim rate
-   temporal accuracy

------------------------------------------------------------------------

## Task 9.5 --- End-to-End Metrics

Measure:

-   task success rate
-   latency
-   MCP calls
-   agent steps
-   token usage

------------------------------------------------------------------------

## Task 9.6 --- Baseline Comparison

Compare:

``` text
keyword only
vector only
hybrid
hybrid + agent
hybrid + agent + auditor
```

------------------------------------------------------------------------

## Task 9.7 --- Write Evaluation Report

Create:

``` text
docs/evaluation.md
```

Include:

-   methodology
-   results
-   failures
-   improvements
-   limitations

------------------------------------------------------------------------

## Task 9.8 --- Phase 9 Checkpoint

The project now has quantitative evidence showing which architecture
decisions helped.

Commit:

``` text
phase-9-evaluation
```

------------------------------------------------------------------------

# PHASE 10 --- Production Hardening

Only now add infrastructure based on actual bottlenecks.

## Task 10.1 --- Structured Logging

Add:

-   request ID
-   investigation ID
-   user ID
-   event ID
-   tool call ID

------------------------------------------------------------------------

## Task 10.2 --- Health Checks

Implement:

``` text
/health
/ready
```

------------------------------------------------------------------------

## Task 10.3 --- Retry and Timeout Policies

Add to:

-   LLM calls
-   embedding calls
-   external services
-   MCP calls where appropriate

------------------------------------------------------------------------

## Task 10.4 --- Rate Limiting

Protect:

-   ingestion endpoints
-   query endpoints
-   investigation endpoints

------------------------------------------------------------------------

## Task 10.5 --- Redis Decision

Measure first.

If justified, add Redis for:

-   caching
-   rate limiting
-   shared transient state

Document why.

------------------------------------------------------------------------

## Task 10.6 --- Background Processing

If processing blocks ingestion, introduce a queue/worker system.

Move:

-   embeddings
-   memory extraction
-   consolidation

to background jobs.

------------------------------------------------------------------------

## Task 10.7 --- LLM Provider Fallback

Implement provider abstraction.

Example:

``` text
Primary
  ↓ failure
Fallback
```

Only add multiple providers if reliability or development requirements
justify them.

------------------------------------------------------------------------

## Task 10.8 --- OpenTelemetry

Add traces for:

``` text
API
Retrieval
MCP
LLM
Agent
Database
```

------------------------------------------------------------------------

## Task 10.9 --- Security Review

Test:

-   authentication
-   authorization
-   prompt injection
-   SQL injection
-   XSS
-   secret leakage
-   oversized requests
-   cross-user access

------------------------------------------------------------------------

## Task 10.10 --- Load Testing

Measure:

-   ingestion throughput
-   query latency
-   concurrent investigations
-   database performance

------------------------------------------------------------------------

## Task 10.11 --- Phase 10 Checkpoint

The application must be deployable and observable.

Commit:

``` text
phase-10-production-hardening
```

------------------------------------------------------------------------

# PHASE 11 --- Frontend Product Quality

## Task 11.1 --- Chat Interface

Build the primary interaction:

``` text
Ask about your browsing...
```

------------------------------------------------------------------------

## Task 11.2 --- Evidence Cards

Show:

-   source
-   timestamp
-   title
-   relevant snippet

------------------------------------------------------------------------

## Task 11.3 --- Timeline

Add interactive timeline.

------------------------------------------------------------------------

## Task 11.4 --- Investigation Trace

Show:

``` text
Plan
→ Tools
→ Evidence
→ Audit
→ Answer
```

------------------------------------------------------------------------

## Task 11.5 --- Memory Explorer

Show:

-   memories
-   sessions
-   topics
-   research threads

Only expose features that actually exist.

------------------------------------------------------------------------

## Task 11.6 --- Privacy Controls

Add:

-   pause
-   delete
-   retention
-   export

------------------------------------------------------------------------

# PHASE 12 --- Advanced Extensions

These are intentionally AFTER the core project.

Choose only the extensions that make the project more interesting.

## Extension 12.1 --- Research Threads

Group multiple sessions into a continuing investigation.

------------------------------------------------------------------------

## Extension 12.2 --- Recurring Interests

Detect topics repeatedly researched over time.

------------------------------------------------------------------------

## Extension 12.3 --- Entity Relationships

Track:

``` text
Technology
→ Website
→ Topic
→ Session
→ Memory
```

------------------------------------------------------------------------

## Extension 12.4 --- Memory Consolidation

Merge many low-level memories into higher-level persistent memories.

------------------------------------------------------------------------

## Extension 12.5 --- Memory Decay

Reduce importance of stale memories.

Do not delete evidence automatically.

------------------------------------------------------------------------

## Extension 12.6 --- Knowledge Graph

Only if relationship queries justify it.

------------------------------------------------------------------------

## Extension 12.7 --- Goal Detection

Infer possible goals from repeated activity.

Always label as inference.

------------------------------------------------------------------------

## Extension 12.8 --- Recommendations

Suggest:

-   previous relevant research
-   related memories
-   unfinished research threads

------------------------------------------------------------------------

## Extension 12.9 --- User Feedback

Allow users to mark answers:

-   correct
-   incorrect
-   partially correct
-   evidence missing

Use feedback for evaluation.

------------------------------------------------------------------------

## Extension 12.10 --- Local-Only Mode

Run the full AI pipeline with local models.

Example:

``` text
Lyzr, Groq, and Gemini
+
local embeddings
+
PostgreSQL
```

------------------------------------------------------------------------

# PHASE 13 --- Resume and Interview Preparation

## Task 13.1 --- Measure Real Metrics

Never put invented numbers on the resume.

Measure:

-   number of events processed
-   retrieval Recall@K
-   MRR
-   evidence coverage
-   latency
-   task success rate
-   hallucination/unsupported claim rate
-   ingestion throughput

------------------------------------------------------------------------

## Task 13.2 --- Architecture Document

Be able to explain:

``` text
Why PostgreSQL?
Why pgvector?
Why hybrid retrieval?
Why MCP?
Why agents?
Why FastAPI?
Why background processing?
Why Redis, if used?
Why not Kafka?
Why not Elasticsearch?
Why not a dedicated vector DB?
Why not microservices?
```

------------------------------------------------------------------------

## Task 13.3 --- ADRs

Create Architecture Decision Records for important decisions.

Examples:

``` text
ADR-001 PostgreSQL
ADR-002 pgvector
ADR-003 Hybrid Retrieval
ADR-004 MCP
ADR-005 Modular Monolith
ADR-006 LLM Provider Abstraction
```

Each ADR should contain:

-   context
-   decision
-   alternatives
-   tradeoffs
-   consequences

------------------------------------------------------------------------

## Task 13.4 --- Failure Stories

Document real failures.

Examples:

-   retrieval returned irrelevant evidence
-   temporal query failed
-   LLM hallucinated
-   API was rate limited
-   duplicate events occurred
-   embedding failed

Then document the fix.

These are extremely valuable in interviews.

------------------------------------------------------------------------

## Task 13.5 --- Demo

Prepare a 5-minute demo:

1.  Show browser activity.
2.  Show captured events.
3.  Show sessionization.
4.  Ask a question.
5.  Show retrieval.
6.  Show MCP calls.
7.  Show evidence.
8.  Show audit.
9.  Show answer.
10. Show evaluation metrics.

------------------------------------------------------------------------

# FINAL IMPLEMENTATION ORDER

Do NOT change this order unless a real engineering dependency requires
it.

``` text
1. Repository
2. Development environment
3. Docker
4. Event schema
5. PostgreSQL
6. Event ingestion
7. Browser extension
8. Deduplication
9. Privacy
10. Sessions
11. Timeline
12. Deterministic search
13. Basic question answering
14. Memory
15. Embeddings
16. pgvector
17. Hybrid retrieval
18. Evaluation
19. MCP
20. Agent workflow
21. Auditor
22. Investigation trace
23. Production hardening
24. Frontend refinement
25. Advanced extensions
26. Resume metrics
27. Interview preparation
```

The key rule is:

> Never add a technology just because it sounds impressive.

Before adding anything, answer:

``` text
What problem am I solving?

Why is the current architecture insufficient?

Why this technology?

What alternative did I consider?

What tradeoff does it introduce?

How will I measure whether it helped?
```

If those questions cannot be answered, postpone the feature.

------------------------------------------------------------------------

# FINAL MILESTONE

The project has reached its ideal interview-ready state when the
following statement is true:

> "I started with a modular monolith that ingested browser events into
> PostgreSQL. I added deterministic sessionization and retrieval first.
> When semantic queries became necessary, I introduced embeddings and
> pgvector. I evaluated keyword, vector and hybrid retrieval rather than
> assuming one was better. I then exposed the retrieval capabilities
> through MCP and built an agentic investigation workflow with evidence
> auditing. Finally, I added production concerns such as privacy,
> observability, retries, caching and background processing only where
> measurements justified them."

That story is more valuable than saying:

> "I used 25 AI technologies."
