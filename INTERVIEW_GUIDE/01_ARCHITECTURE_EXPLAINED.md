# 01: Complete System Architecture Explained

```
                                  +---------------------------------------+
                                  |       Browser Extension / Agent       |
                                  |   (Captures clicks, urls, inputs)     |
                                  +---------------------------------------+
                                                      |
                                                      v  HTTP POST / Sync
                                  +---------------------------------------+
                                  |  Sync Log & Ingestion Layer           |
                                  |  - apps/api/services/sync_log.py      |
                                  |  - Privacy Sanitization & Normalizer  |
                                  +---------------------------------------+
                                                      |
                                                      v  Inserts
+----------------------------------------------------------------------------------------------------------------+
|                                     Storage Layer (SQLite / PostgreSQL)                                        |
|  - Event (Raw & Normalized)   - BrowserSession (30-min window)   - Memory & Evidence   - DiscoveryResult       |
+----------------------------------------------------------------------------------------------------------------+
        |                                             |                                             |
        v                                             v                                             v
+-----------------------------+             +-------------------------------+             +----------------------+
|  Local ML Engines           |             |  Multi-Route Orchestration    |             |  Model Context       |
|  - TF-IDF + Naive Bayes     |             |  - apps/api/services/         |             |  Protocol (MCP)      |
|    (apps/api/services/      |             |    orchestrator.py            |             |  - apps/mcp/server.py|
|     classifier.py)          |             |  Route 1: Fuzzy Keyword       |             |  15 Composable Tools |
|  - MiniBatchKMeans Cluster  |             |  Route 2: Preference Infer    |             +----------------------+
|    (clustering.py)          |             |  Route 3: Hypothesis Compare  |                        |
|  - IsolationForest Anomaly  |             |  Route 4: SQL Domain/Time     |                        |
|    (anomaly_detection.py)   |             |  Route 5: Dense Hybrid Search |                        |
|  - Cosine Recommendations   |             |  Route 6: Memory Lookup       |                        |
|    (recommendation.py)      |             +-------------------------------+                        |
+-----------------------------+                               |                                      |
        |                                                     v                                      |
        |                                   +-----------------------------------+                    |
        |                                   |  Evidence Fusion & Neural Rerank  |                    |
        |                                   |  - Reciprocal Rank Fusion (RRF)   |                    |
        |                                   |  - services/reranker.py           |                    |
        |                                   +-----------------------------------+                    |
        |                                                     |                                      |
        |                                                     v                                      |
        |                                   +-----------------------------------+                    |
        |                                   |  Investigation Engine             |                    |
        |                                   |  - services/investigation.py      |<-------------------+
        |                                   |  - services/agentic_investigator  |
        |                                   +-----------------------------------+
        |                                                     |
        |                                      +--------------+--------------+
        |                                      |                             |
        |                                      v (API Key Available)         v (Offline / No Key)
        |                               +------------------+         +-------------------------+
        |                               | Groq LLM API     |         | Deterministic Rule-     |
        |                               | (Llama-3.3-70B)  |         | Based Synthesizer       |
        |                               +------------------+         +-------------------------+
        |                                      |                             |
        |                                      +--------------+--------------+
        |                                                     |
        v                                                     v
+----------------------------------------------------------------------------------------------------------------+
|                                    Presentation & Dashboards Layer (Next.js 14)                                |
|  - /twin (Digital Twin)    - /wellbeing (Digital Wellbeing)    - /dashboard (Intelligence Hub)    - /chat       |
+----------------------------------------------------------------------------------------------------------------+
```

---

## Component-by-Component Breakdown

### 1. Ingestion, Sanitization & Normalization
- **File**: `apps/api/services/sync_log.py`, `apps/api/utils/privacy.py`, `apps/api/utils/normalization.py`
- **What it is**: Ingests JSON event lines from `events.log` or API requests into SQLite/Postgres.
- **Why it exists**: Raw browser logs contain sensitive headers, auth tokens, passwords, and malformed event types (`input` vs `input_submitted`). This layer standardizes schema and strips PII before database entry.
- **Input**: Raw JSON payload or `events.log`.
- **Output**: Validated SQLAlchemy `Event` models inserted into the database.
- **Connects to**: `Event` table in `demo.db`.

### 2. Sessionization
- **File**: `apps/api/utils/sessionization.py`, `apps/api/services/sessions.py`
- **What it is**: Groups chronologically ordered browser events into contiguous sessions using a 30-minute inactivity threshold.
- **Why it exists**: Users do not browse continuously. Computing focus scores and deep work intervals requires knowing when a work block starts and ends.
- **Input**: List of `Event` objects ordered by timestamp.
- **Output**: `BrowserSession` records containing `start_time`, `end_time`, `duration_seconds`, `event_count`, and `domain_frequencies`.
- **Connects to**: `BrowserSession` table and Wellbeing focus calculations.

### 3. Multi-Route Retrieval Orchestrator
- **File**: `apps/api/services/orchestrator.py` (`GeneralizedInvestigationOrchestrator`)
- **What it is**: An evidence discovery engine running 6 parallel search strategies.
- **Why it exists**: A single search method fails on diverse questions. For example, *"Did I search Dostoevsky?"* needs exact fuzzy token matching, while *"What is my favourite programming language?"* needs preference aggregation over 400+ events.
- **Input**: Natural language user query string.
- **Output**: Unified dictionary with candidate events grouped by route, individual route hit counts, and initial relevance weights.
- **Connects to**: Reciprocal Rank Fusion & Reranker.

### 4. Hybrid Search & Vector Store
- **File**: `apps/api/services/search.py`, `apps/api/services/vector_store.py`, `apps/api/services/embeddings.py`
- **What it is**: Combines keyword SQL filtering (`ILIKE` / Postgres Full-Text Search) with 384-dimensional dense semantic vectors.
- **Why it exists**: Keyword search captures exact terms (e.g. `8051`); vector search captures semantic synonyms (e.g. `microcontroller timers`).
- **Input**: Query string + optional domain and timestamp filters.
- **Output**: Ranked candidate event IDs.
- **Connects to**: Reciprocal Rank Fusion (RRF).

### 5. Evidence Fusion & Neural Reranker
- **File**: `apps/api/services/reranker.py` (`NeuralReranker`)
- **What it is**: Bi-encoder vector cosine scorer that takes candidate evidence items and computes dot product similarity with the query vector.
- **Why it exists**: Initial retrieval routes produce false positives. The reranker scores each candidate using: `(0.85 * semantic_cosine_score) + (0.15 * initial_retrieval_score)`.
- **Input**: List of candidate `Evidence` objects + Query string.
- **Output**: Re-sorted top-N `Evidence` items.
- **Connects to**: Grounded Answer Synthesizer.

### 6. Grounded Answer Synthesizer
- **File**: `apps/api/services/investigation.py` (`run_investigation`)
- **What it is**: Compiles retrieved browser records into a structured context window and generates an answer strictly constrained by evidence.
- **Why it exists**: Prevents LLM hallucinations. If Groq API is reachable, it uses `llama-3.3-70b-versatile` with an explicit anti-hallucination prompt. If offline or without an API key, it triggers the deterministic synthesizer.
- **Input**: Query + Top verified `Evidence` records.
- **Output**: Grounded response string + Evidence citations (`CONFIRMED`, `LIKELY`, `NOT FOUND`).
- **Connects to**: HTTP API endpoints & MCP server tools.

### 7. Supervised ML Classifier
- **File**: `apps/api/services/classifier.py` (`BrowserEventClassifier`)
- **What it is**: `TfidfVectorizer` + `MultinomialNB` pipeline trained to classify text into 10 categories (`programming/development`, `education`, `research`, `entertainment`, etc.).
- **Why it exists**: Quickly tags events for behavioral profiling without making costly LLM API calls for every page visit.
- **Input**: Text blob combining title, URL, search input, and domain.
- **Output**: `MLClassificationResult` with predicted category and calibrated class probability dictionary.

### 8. Unsupervised Clustering & Anomaly Detection
- **File**: `apps/api/services/clustering.py` & `apps/api/services/anomaly_detection.py`
- **What it is**: `MiniBatchKMeans` for grouping dense vector representations of browser history, and `IsolationForest` for detecting statistical outliers across 5 behavioral dimensions (`[hour, is_weekend, dom_rarity, input_len, title_len]`).
- **Why it exists**: Discovers latent interest topics autonomously and flags irregular late-night browsing spikes or rare domains.

### 9. MCP (Model Context Protocol) Server
- **File**: `apps/mcp/server.py`, `apps/mcp/tools.py`
- **What it is**: Fast asynchronous standard I/O (stdio) MCP server exposing 15 tools.
- **Why it exists**: Allows external agent frameworks (Claude Desktop, Cursor, Lyzr) to natively query the local browser intelligence system.
