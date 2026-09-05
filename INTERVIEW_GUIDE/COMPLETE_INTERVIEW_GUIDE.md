# BrowserMCP - Complete Master Interview Guide

> This unified document compiles all 17 interview preparation and technical deep-dive guides into a single comprehensive manual.

---
<!-- ========================================== -->
<!-- SECTION: 00_PROJECT_IN_ONE_PAGE.md -->
<!-- ========================================== -->

# 00: Project In One Page

## 1. What Problem This Project Solves
Modern browsers capture vast amounts of interaction history, but search histories are unstructured, ephemeral, and noisy (e.g. ad requests, tracking iframes, duplicate page clicks).
When users want to ask natural-language questions about their own digital history (*"What programming language did I explore most?"*, *"Did I look up Dostoevsky?"*, *"What were my longest focus sessions?"*), standard browser search fails because:
1. Keyword lookup misses semantic variants, sub-topics, and conceptual links.
2. Standard AI chatbots hallucinate answers because they have no access to actual local browsing records or evidence citations.

**BrowserMCP** solves this by providing a **privacy-first, locally indexed Personal Browser Intelligence & Digital Twin engine**. It ingests raw browser extension events, sanitizes PII, applies multi-route retrieval + statistical machine learning (clustering, anomaly detection, TF-IDF classification), and performs **evidence-grounded AI synthesis** where every claim is classified as `CONFIRMED`, `LIKELY`, or `NOT FOUND` with direct database citations.

---

## 2. What the Input Is
The system ingests raw JSON event logs captured by the browser extension (`events.log` / `POST /api/v1/events`):
```json
{
  "timestamp": "2026-08-16T10:02:37.527Z",
  "url": "https://stackoverflow.com/questions",
  "pageTitle": "Newest Questions - Stack Overflow",
  "event": "input_submitted",
  "input": "java 8 vs java 15"
}
```
Event types include: `page_loaded`, `input_submitted`, `search_submitted`, `click`, `link_clicked`, and `page_content`.

---

## 3. End-to-End Execution Flow (Browser Event → Final Answer)

```
[ Browser Extension ]
        │  (Captures clicks, inputs, urls, titles, page text)
        ▼
[ Auto-Sync Middleware & Privacy Sanitization ]
        │  (Strips secrets, auth tokens, passwords; normalizes EventType enum)
        ▼
[ SQLite / Postgres Storage (`demo.db`) ]
        │  (Stores Event, BrowserSession, Memory, DiscoveryResult tables)
        ▼
[ User Natural Language Query ("What is my favourite programming language?") ]
        ▼
[ Generalized Investigation Orchestrator ]
  ├── Route 1: Exact & Fuzzy Keyword Matching (`utils/fuzzy.py`)
  ├── Route 2: Category Preference Inference (`services/preference.py`)
  ├── Route 3: Contrast / Hypothesis Comparison (`services/general_inference.py`)
  ├── Route 4: Structured SQL Filtering (domains, inputs, date windows)
  ├── Route 5: Dense Hybrid Semantic Search (`services/search.py`)
  └── Route 6: Long-Term Memory Lookup (`services/memory.py` via vector store)
        ▼
[ Evidence Fusion & Neural Reranker ]
        │  (Reciprocal Rank Fusion + Bi-Encoder Cosine Reranking in `services/reranker.py`)
        ▼
[ Grounded Synthesis Engine (`services/investigation.py`) ]
        ├── If Groq API Key Present: Groq LLM (llama-3.3-70b) with strict anti-hallucination prompt
        └── If Offline / No API Key: Deterministic Rule-Based Evidence Synthesizer
        ▼
[ Final Output with Grounded Citations & Status (`CONFIRMED` / `LIKELY` / `NOT FOUND`) ]
```

---

## 4. Main Technologies Used
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Uvicorn, SQLite / PostgreSQL (`pgvector`).
- **Machine Learning & NLP**: Scikit-Learn (`MultinomialNB`, `TfidfVectorizer`, `HashingVectorizer`, `MiniBatchKMeans`, `IsolationForest`), NumPy, Cosine Similarity.
- **LLM / Generative AI**: Groq API (`llama-3.3-70b-versatile`) with deterministic fallback synthesis.
- **Protocol**: Anthropic Model Context Protocol (MCP) Python SDK (`mcp.server.lowlevel`).
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, TailwindCSS / Custom Glassmorphism CSS.

---

## 5. Top 8 Most Important Components & Files

1. **Multi-Route Orchestrator** (`apps/api/services/orchestrator.py`): Runs 6 parallel retrieval strategies so queries don't fail on a single missed keyword or synonym.
2. **Investigation Service** (`apps/api/services/investigation.py`): Manages the investigation lifecycle, compiles context, and generates grounded answers.
3. **Agentic Investigator** (`apps/api/services/agentic_investigator.py`): Multi-step autonomous agent with step budgets, tool calling, and loop protection.
4. **Preference & Category Inference** (`apps/api/services/preference.py`): Scans input strings, search tokens, and domain visits to quantify user affinities.
5. **Supervised Classifier** (`apps/api/services/classifier.py`): TF-IDF + Multinomial Naive Bayes pipeline classifying web visits into 10 categories.
6. **Unsupervised Clustering** (`apps/api/services/clustering.py`): `MiniBatchKMeans` with TF-IDF keyword extraction discovering interest topics.
7. **Anomaly Detection** (`apps/api/services/anomaly_detection.py`): `IsolationForest` detecting anomalous browsing hours and rare domains.
8. **Digital Twin & Wellbeing Service** (`apps/api/services/twin.py` & `wellbeing.py`): Builds behavioral models, 24h heatmaps, focus scores, and interest graph topologies.

---

## 6. The 60-Second Interview Explanation

> *"BrowserMCP is an applied AI system and Model Context Protocol (MCP) server that turns raw, unstructured browser history into an evidence-grounded personal intelligence model. Instead of relying solely on an LLM or basic keyword search, we built a hybrid retrieval and deterministic ML architecture. 
> 
> When raw browser events arrive, they are sanitized and stored in SQLite/PostgreSQL. When a user asks a question, our Generalized Investigation Orchestrator executes six parallel retrieval routes—including fuzzy entity matching, dense vector embeddings, structured SQL filtering, and preference heuristics. Results are fused using Reciprocal Rank Fusion and reranked using a bi-encoder cosine scorer. 
> 
> Finally, the synthesized answer is grounded against actual database records, classifying claims strictly as CONFIRMED, LIKELY, or NOT FOUND with direct citations so the system never hallucinates."*

---

## 7. The 3-Minute Deep Dive Explanation

> *"The core challenge with personal browser data is that it is noisy, high-dimensional, and full of ad tracking iframes, typos, and implicit signals. If you simply pass raw history to an LLM, you hit context window limits, privacy risks, and hallucinations.
> 
> In this project, we built a three-layer architecture:
> 
> **Layer 1 is Data Ingestion & Sanitization**: Browser events stream in via an extension or JSON log. The ingestion pipeline strips sensitive query parameters and passwords, normalizes event types, and clusters raw timestamps into 30-minute session blocks.
> 
> **Layer 2 is Local Machine Learning & Retrieval**: Rather than making expensive neural calls for everything, we use targeted ML components:
> - Supervised TF-IDF + Multinomial Naive Bayes for 10-class web activity categorization.
> - Unsupervised MiniBatchKMeans for discovering emergent interest clusters and extracting top TF-IDF keywords.
> - Isolation Forest running on a 5-dimensional feature space to detect behavioral anomalies like late-night browsing spikes or rare domain visits.
> - Hybrid Retrieval combining SQLite/Postgres full-text search with dense 384-dimensional subword hashing embeddings, blended via Reciprocal Rank Fusion (RRF) and scored by a bi-encoder neural reranker.
> 
> **Layer 3 is the Agentic & Investigation Engine**: When answering complex questions, our Orchestrator runs multi-route parallel retrieval. If an LLM API key (like Groq) is present, it formats retrieved evidence into a strictly bounded system prompt. If offline, our deterministic rule engine synthesizes the answer. Every output includes verified evidence UUIDs and a confidence rating (CONFIRMED, LIKELY, or NOT FOUND).
> 
> We also exposed this entire intelligence layer through 15 composable MCP tools, allowing external AI assistants (like Claude or Cursor) to securely query the user's browser knowledge base."*


---

<!-- ========================================== -->
<!-- SECTION: 01_ARCHITECTURE_EXPLAINED.md -->
<!-- ========================================== -->

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


---

<!-- ========================================== -->
<!-- SECTION: 02_CODE_WALKTHROUGH.md -->
<!-- ========================================== -->

# 02: Real Code Walkthrough

This document traces actual, step-by-step code execution for 4 representative user queries across the repository.

---

## Example 1: "What is my favourite programming language?"

### 1. Endpoint & Initial Trigger
- **HTTP Route**: `POST /api/v1/query` in `apps/api/routes/timeline.py` or MCP Tool `investigate(question="What is my favourite programming language?")`.
- **Function Called**: `run_investigation(db, query="What is my favourite programming language?")` in `apps/api/services/investigation.py`.

### 2. Auto-Sync & Investigation Record Initialization
1. `sync_events_log_to_db()` runs in `services/sync_log.py` to ensure all latest `events.log` lines are written to SQLite.
2. An `Investigation` row is created with status `"started"` in the database.

### 3. Query Expansion & Multi-Route Retrieval
- `GeneralizedInvestigationOrchestrator.execute_multi_route_retrieval(db, query)` is called in `services/orchestrator.py`:
  - `rewrite_and_expand_query` identifies `category_hint = "programming_language"` (via `services/preference.py:detect_preference_category`).
  - **Route 2 (Category Preference)** triggers:
    - Calls `infer_programming_preference(db)` in `services/preference.py`.
    - Scans all database events looking for tokens in `LANGUAGES` (`java`, `python`, `typescript`, `cpp`, `rust`, etc.) across `input_text`, URL parameters, and titles.
    - Weighs inputs: searches count as +5.0 points, titles count as +2.0 points, URLs count as +1.0 point.
    - Aggregates scores:
      - `Java`: 28 points (found searches: `"java 8 vs java 15"`, `"spring boot 3 batch insert"`, `"spring cloud gateway"`).
      - `Python`: 8 points (found: `"python list comprehension"`).
      - `TypeScript`: 4 points.
    - Detects highest scoring candidate: `Java` (Score: 28.0, Count: 14 events).
    - Status set to `LIKELY` (or `CONFIRMED` if explicit keyword like "favourite" was typed).
  - **Route 5 (Dense Hybrid Semantic)** triggers:
    - Generates 384-d vector for `"What is my favourite programming language?"` using `services/embeddings.py:embed_text`.
    - Computes cosine dot product across all stored event vectors.
    - Blends with keyword search using Reciprocal Rank Fusion (RRF with $k=60$) in `services/search.py:search_hybrid`.

### 4. Evidence Fusion & Neural Reranker
- `candidates_by_route` merges all events into `fused_events` (14 Java events + 3 Python events).
- `NeuralReranker.rerank_evidence(query, evidence_list, top_n=30)` in `services/reranker.py` scores each candidate against the query vector using $(0.85 \times \text{semantic}) + (0.15 \times \text{initial\_score})$.

### 5. Grounded Synthesis
- If `GROQ_API_KEY` is set:
  - Formats top 40 retrieved events into context and prompts Groq (`llama-3.3-70b-versatile`).
- If Offline / Fallback (lines 301–314 in `services/investigation.py`):
  - Evaluates `pref_data`:
  ```python
  cand = "Java"
  conf = "LIKELY"
  summary = "**Java** is your likely preferred programming language, based on your repeated Java-related activity such as 'java 8 vs java 15' across your browser history (14 supporting events)."
  ```
- Returns `Investigation` object + list of 14 `Evidence` citations with UUIDs.

---

## Example 2: "Did I search Dostoevsky?"

### 1. Endpoint & Initial Trigger
- **Route**: `POST /api/v1/query` ➔ `run_investigation(db, "Did I search Dostoevsky?")`.

### 2. Multi-Route Retrieval
- `rewrite_and_expand_query` in `services/orchestrator.py`:
  - `extract_entity_candidate("Did I search Dostoevsky?")` extracts token `"Dostoevsky"`.
  - Recognizes `is_strict_entity_check = True`.
- **Route 1 (Exact & Fuzzy Entity Match)**:
  - Scans all events with `find_entity_matches_in_text("Dostoevsky", text_blob, threshold=0.75)` in `utils/fuzzy.py`.
  - Calculates Levenshtein distance ratio using Python's `difflib.SequenceMatcher`.
  - Database contains 0 occurrences of "Dostoevsky" (or similar spelling).
  - `candidates_by_route["entity_fuzzy"]` = `[]`.
- **Route 5 (Hybrid Semantic Search)**:
  - Vector cosine similarity finds low-similarity general literature pages (similarity < 0.35).

### 3. Strict Verification & Fallback Synthesis
- In `services/investigation.py` (lines 190–200):
  - Because `is_strict_entity_check` is true, it strictly filters `fused_events` to only those matching `"Dostoevsky"`.
  - Filtered event count is 0.
- Fallback Synthesis (lines 280–282):
  ```python
  summary = "**NOT FOUND / UNAVAILABLE:** The captured browsing data does not contain any evidence or searches for **'Dostoevsky'**."
  ```
- Confidence: `NOT FOUND`, Evidence count: 0.

---

## Example 3: "What did I search yesterday?"

### 1. Endpoint & Initial Trigger
- **Route**: `POST /api/v1/query` ➔ `run_investigation(db, "What did I search yesterday?")`.

### 2. Query Expansion & Temporal SQL Filter
- `rewrite_and_expand_query` in `services/orchestrator.py`:
  - Detects temporal token `"yesterday"`.
  - Sets `time_start = now - timedelta(days=2)` and `time_end = now`.
- **Route 4 (Structured SQL Filter)**:
  - Executes SQL query:
    ```python
    db.query(Event).filter(Event.timestamp >= time_start, Event.timestamp <= time_end).all()
    ```
  - Retrieves all events logged in that 48-hour timestamp window.
- **Route 6 (Behavioral Mining)**:
  - Filters for events where `input_text != None` or URL contains search parameters (`extract_url_search_params(e.url)`).

### 3. Synthesis & Citation Attachment
- Collects 18 search input events (e.g. `"spring boot 3 batch insert"`, `"model context protocol"`).
- Groq / Fallback synthesizer compiles bullet points formatted with exact timestamps:
  ```
  **CONFIRMED / LIKELY EVIDENCE FOUND:** Retrieved 18 relevant browsing records matching your query:
  - 'spring boot 3 batch insert' at 2026-08-20T11:05:12Z
  - 'model context protocol specification' at 2026-08-20T11:14:30Z
  ```
- All 18 events attached with `relevance >= 0.8`.

---

## Example 4: "What have you learned about me?"

### 1. Endpoint & Initial Trigger
- **Route**: `GET /api/v1/twin` (for dashboard) or `POST /api/v1/query` (for conversational chat).

### 2. Digital Twin Model Synthesis
- `DigitalTwinService.get_digital_twin_model(db)` in `apps/api/services/twin.py`:
  1. Queries all 485+ events from SQLite.
  2. Runs `InterestClusterEngine.discover_clusters(db, n_clusters=5)`:
     - Vectorizes event text into 384-d dense embeddings.
     - Performs `MiniBatchKMeans(n_clusters=5)`.
     - Uses `TfidfVectorizer` on cluster texts to extract the top 4 keywords per cluster (e.g., Cluster 1: `["Spring", "Cloud", "Redis", "Gateway"]`).
  3. Evaluates domain distributions (`Counter(e.domain)`):
     - `stackoverflow.com`: 48 visits, `github.com`: 32 visits, `youtube.com`: 26 visits, `instagram.com`: 18 visits.
  4. Runs `infer_programming_preference`, `infer_philosophy_preference`, and `infer_art_form_preference`.
  5. Computes Behavioral Traits:
     - Trait 1: *Analytical & Systems-Oriented Problem Solving* (Confidence: `CONFIRMED`, 92%, Grounded in 85 events).
     - Trait 2: *Theoretical & Existential Curiosity* (Confidence: `LIKELY`, 86%, Grounded in 32 events).
     - Trait 3: *Deep Focused Work Spurt Behavior* (Confidence: `CONFIRMED`, 88%, Grounded in 8 long sessions).
     - Trait 4: *Recreational Media Susceptibility* (Confidence: `CONFIRMED`, 78%, Grounded in 44 social media events).
  6. Assembles Cross-Domain Curiosity Trajectories:
     - E.g. *Spring Framework ➔ Model Context Protocol* (Novelty: 94%).
  7. Constructs Interactive Topology Graph:
     - Generates 32 nodes (Twin Core, 5 Cluster Nodes, 20 Keyword Nodes, 6 Domain Nodes) and 31 relational edges.

### 3. Final Response Delivery
- Returns structured JSON to the Next.js frontend at `/twin` rendering the 10 visual panes and conversational chat interface.


---

<!-- ========================================== -->
<!-- SECTION: 03_AI_TECHNIQUES.md -->
<!-- ========================================== -->

# 03: AI & Machine Learning Techniques

This document details every genuine AI, ML, and NLP technique implemented in the codebase.

---

## Breakdown: What is Real ML vs Deterministic vs LLM

| Technique | Category | File Path | Implementation Reality |
| :--- | :--- | :--- | :--- |
| **Supervised Classifier** | Traditional ML (Supervised) | `apps/api/services/classifier.py` | `TfidfVectorizer` + `MultinomialNB` in Scikit-Learn |
| **Unsupervised Interest Clusters** | Traditional ML (Unsupervised) | `apps/api/services/clustering.py` | `MiniBatchKMeans` with TF-IDF keyword extraction |
| **Anomaly Detection** | Traditional ML (Unsupervised) | `apps/api/services/anomaly_detection.py` | `IsolationForest` on 5-d behavioral feature vectors |
| **Local Dense Embedder** | Statistical Subword Projection | `apps/api/services/embeddings.py` | `HashingVectorizer` (Char 1-3 ngrams + Word 1-2 ngrams) with L2 normalization (Deterministic 384-d vector; not a deep neural network) |
| **Remote Neural Embeddings** | Deep Neural Network (API) | `apps/api/services/embeddings.py` | Google Gemini `embedding-001` or Ollama `nomic-embed-text` |
| **Hybrid Search & RRF** | Information Retrieval (IR) | `apps/api/services/search.py` | SQL Full-Text / `ILIKE` + Vector Cosine + Reciprocal Rank Fusion |
| **Bi-Encoder Neural Reranker** | Dense Vector Scoring | `apps/api/services/reranker.py` | Vector cosine dot product re-weighting $(0.85 \times \text{sem} + 0.15 \times \text{init})$ |
| **Content Recommendations** | Vector Proximity Recommender | `apps/api/services/recommendation.py` | Cosine similarity between cluster centroids and topic candidates |
| **Agentic Loop** | Agentic AI / Tool Calling | `apps/api/services/agentic_investigator.py` | Multi-step loop with step budget, tool calling trace & reflection |
| **Answer Synthesis** | Large Language Model (GenAI) | `apps/api/services/investigation.py` | Groq `llama-3.3-70b-versatile` with anti-hallucination prompt |
| **Preference & Entity Engine** | Deterministic Heuristics & NLP | `apps/api/services/preference.py`, `fuzzy.py` | Levenshtein ratio, token frequencies, weighted scoring rules |

---

## 1. Supervised Event Classifier (Multinomial Naive Bayes + TF-IDF)

### Concept
Given browser page text, search inputs, and domain names, determine which of 10 categories (`programming/development`, `education`, `research`, `entertainment`, `shopping`, `social`, `news`, `finance`, `travel`, `other`) the visit belongs to.

### Exact Implementation
- **File**: `apps/api/services/classifier.py`
- **Pipeline**:
  ```python
  pipeline = Pipeline([
      ('tfidf', TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, max_features=2500)),
      ('clf', MultinomialNB(alpha=0.1))
  ])
  ```
- **Inputs**: Composite text string = `input_text + page_title + url + domain`.
- **Outputs**: `MLClassificationResult` with `top_category`, `confidence` score (0.0–1.0), and full `probabilities` dictionary across all 10 classes.
- **Artifact**: Trained and persisted to `classifier_pipeline.joblib`.
- **What happens without it**: The system would have to rely on expensive LLM calls for every event or rigid hardcoded domain regexes.
- **Interview Question**: *"Why use Multinomial Naive Bayes over a BERT-based transformer for browser event classification?"*
- **Good Answer**: *"Multinomial Naive Bayes with sublinear TF-IDF trains in milliseconds, requires zero GPU memory, and executes inference in under 1ms per event. For lightweight real-time background classification of hundreds of browser events, it provides high macro F1 (94%+) with near-zero latency."*

---

## 2. Unsupervised Interest Clustering (MiniBatchKMeans + TF-IDF)

### Concept
Automatically discover what topics the user spends time on without requiring pre-labeled categories.

### Exact Implementation
- **File**: `apps/api/services/clustering.py`
- **Algorithm**:
  1. Computes 384-dimensional dense vectors for all stored events via `embed_batch`.
  2. Runs `MiniBatchKMeans(n_clusters=n_clusters, batch_size=100, random_state=42)`.
  3. Computes cluster semantic coherence = mean cosine similarity between member event vectors and the cluster centroid.
  4. Applies `TfidfVectorizer(max_features=50, stop_words='english')` across documents within each cluster to extract top representative keywords (e.g. `["spring", "redis", "gateway", "boot"]`).
- **What happens without it**: The system cannot surface emergent interests (like a sudden focus on `Model Context Protocol` or `8051 Microcontrollers`) unless someone hardcoded those tags.
- **Interview Question**: *"Why MiniBatchKMeans instead of standard KMeans or DBSCAN?"*
- **Good Answer**: *"MiniBatchKMeans processes subsets of vectors in memory chunks, significantly reducing computational overhead and memory usage on live streaming event data. DBSCAN could also work, but MiniBatchKMeans guarantees a bounded number of high-coherence clusters suitable for dashboard rendering."*

---

## 3. Anomaly Detection (Isolation Forest)

### Concept
Detect unusual or outlier browsing events that deviate significantly from the user's historical baseline behavior.

### Exact Implementation
- **File**: `apps/api/services/anomaly_detection.py`
- **Feature Vector (5 Dimensions)**:
  1. `Hour of Day` ($0.0 - 23.0$)
  2. `Is Weekend` ($0.0 \text{ or } 1.0$)
  3. `Domain Rarity` ($\frac{1}{\text{Domain Count}}$)
  4. `Input Text Length`
  5. `Page Title Length`
- **Model**:
  ```python
  model = IsolationForest(contamination=0.05, random_state=42)
  model.fit(feature_matrix)
  scores = model.decision_function(feature_matrix)
  ```
- **Reason Generation**: Translates anomalous feature dimensions into human-readable explanations (e.g., *"Unusual late-night activity at 2:00 AM"*, *"First-time visit to rare domain 'gumi.criteo.com'"*).
- **Interview Question**: *"How does Isolation Forest isolate anomalies?"*
- **Good Answer**: *"Isolation Forest builds an ensemble of random decision trees. Because anomalies are few and have distinct feature values, they require fewer random splits to isolate in tree partitions, resulting in shorter average path lengths from the root."*

---

## 4. Local Dense Embedder (Subword Character & Word N-Gram Hashing)

### Concept
Provides an offline, deterministic semantic dense vector representation for text without downloading multi-gigabyte neural checkpoints or requiring internet API access.

### Exact Implementation
- **File**: `apps/api/services/embeddings.py` (`LocalDenseSemanticEmbedder`)
- **Mechanism**:
  - `HashingVectorizer(n_features=384, ngram_range=(1,3), analyzer="char_wb")` captures morphological roots and typo tolerance.
  - `HashingVectorizer(n_features=384, ngram_range=(1,2), analyzer="word")` captures word-level semantics.
  - Blends matrices: `combined = (0.6 * word_mat) + (0.4 * char_mat)`.
  - Normalizes via L2 Euclidean norm: $\vec{v}_{\text{norm}} = \frac{\vec{v}}{\|\vec{v}\|_2}$.
- **Important Interview Note**: **Do NOT call this a deep transformer model.** It is a fast, deterministic statistical hashing projection with L2 normalization designed for offline dev environments, with automatic switchover to Google Gemini/Ollama when configured.

---

## 5. Hybrid Search & Reciprocal Rank Fusion (RRF)

### Concept
Combine the exact keyword recall of SQL/FTS with the conceptual similarity of dense semantic vectors without needing arbitrary score calibration.

### Exact Implementation
- **File**: `apps/api/services/search.py`
- **RRF Formula**:
  $$\text{Score}_{\text{RRF}}(d) = \sum_{r \in \text{routes}} \frac{1}{k + \text{rank}_r(d)}$$
  Where $k = 60$.
- **Why RRF?**: Vector similarity scores (cosine $0.0 - 1.0$) and SQL BM25/FTS match counts have completely different numerical distributions. RRF uses rank position rather than raw score, preventing one retriever from dominating the other.

---

## 6. Bi-Encoder Neural Reranker

### Concept
Refine top candidate documents returned by initial retrieval routes using dense vector dot-product scoring.

### Exact Implementation
- **File**: `apps/api/services/reranker.py`
- **Formula**:
  $$\text{Final Relevance} = (0.85 \times \text{Semantic Cosine Score}) + (0.15 \times \text{Initial Retrieval Score})$$
- **What it does**: Takes 50 candidate events from multiple routes, computes dense cosine similarity between candidate text (`title + snippet + url`) and the query vector, and sorts descending.


---

<!-- ========================================== -->
<!-- SECTION: 04_EACH_AI_ALGORITHM_FROM_FIRST_PRINCIPLES.md -->
<!-- ========================================== -->

# 04: Each AI Algorithm From First Principles

This document explains the mathematical foundations and intuitive mechanics of each algorithm used in the repository from zero, complete with small numerical examples.

---

## 1. TF-IDF (Term Frequency - Inverse Document Frequency)
*Used in `apps/api/services/classifier.py` and `services/clustering.py`.*

### Intuitive Problem
If the word *"the"* appears 50 times in a document, it is meaningless. If the word *"kubernetes"* appears 5 times, it strongly signals the topic. TF-IDF gives high weight to words that appear frequently in a specific document but rarely across all documents.

### Mathematical Formulation
1. **Term Frequency (TF)**:
   $$\text{TF}(t, d) = \frac{\text{count of } t \text{ in } d}{\text{total words in } d}$$
   *(In our classifier, we use sublinear TF: $\text{TF}_{\text{sublinear}} = 1 + \ln(\text{count})$ if count > 0).*
2. **Inverse Document Frequency (IDF)**:
   $$\text{IDF}(t, D) = \ln\left(\frac{1 + |D|}{1 + \text{count of documents containing } t}\right) + 1$$
3. **TF-IDF Weight**:
   $$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \text{IDF}(t, D)$$

### Concrete Example
- Total Documents $|D| = 100$.
- Document $d_1$: *"python fast api endpoints stackoverflow error"* (6 words).
- Word A: *"python"* appears in 10 documents out of 100.
  - $\text{TF} = 1/6 \approx 0.167$
  - $\text{IDF} = \ln(101 / 11) + 1 = \ln(9.18) + 1 = 2.21 + 1 = 3.21$
  - $\text{TF-IDF} = 0.167 \times 3.21 = \mathbf{0.536}$
- Word B: *"the"* appears in 98 documents out of 100.
  - $\text{IDF} = \ln(101 / 99) + 1 = 0.02 + 1 = 1.02$
  - $\text{TF-IDF} = 0.167 \times 1.02 = \mathbf{0.170}$
- Result: *"python"* receives $3.15\times$ more importance than *"the"*.

---

## 2. Multinomial Naive Bayes
*Used in `apps/api/services/classifier.py`.*

### Intuitive Problem
Given a vector of word counts/TF-IDF weights $\vec{x}$, calculate the probability that the document belongs to category $C_k$ (e.g. `programming/development` vs `entertainment`).

### Mathematical Formulation
Using Bayes' Theorem:
$$P(C_k \mid \vec{x}) = \frac{P(C_k) \prod_{i=1}^n P(x_i \mid C_k)}{P(\vec{x})}$$
Taking logs to prevent floating-point underflow:
$$\log P(C_k \mid \vec{x}) \propto \log P(C_k) + \sum_{i=1}^n x_i \log P(w_i \mid C_k)$$
Where Laplace smoothing with $\alpha = 0.1$ prevents zero probabilities for unseen words:
$$P(w_i \mid C_k) = \frac{\text{Count}(w_i, C_k) + \alpha}{\sum_{w} \text{Count}(w, C_k) + \alpha \cdot |V|}$$

---

## 3. K-Means / MiniBatchKMeans Clustering
*Used in `apps/api/services/clustering.py`.*

### Intuitive Problem
Group $N$ browser event vectors into $K$ topic clusters such that events within the same cluster are semantically similar.

### Mathematical Formulation
Objective: Minimize total Within-Cluster Sum of Squares (Inertia):
$$J = \sum_{j=1}^K \sum_{\vec{x}_i \in S_j} \|\vec{x}_i - \vec{\mu}_j\|^2$$
Where $\vec{\mu}_j$ is the centroid (mean vector) of cluster $S_j$:
$$\vec{\mu}_j = \frac{1}{|S_j|} \sum_{\vec{x} \in S_j} \vec{x}$$

### MiniBatch Optimization
Instead of recalculating centroids over all $N$ vectors in every iteration, MiniBatchKMeans samples small random subsets ($B = 100$ vectors), finds nearest centroids, and performs an incremental gradient update:
$$\vec{\mu}_j \leftarrow (1 - \eta) \vec{\mu}_j + \eta \vec{x}_i$$
Where $\eta = \frac{1}{\text{count}_j}$. This converges dramatically faster on live streams.

---

## 4. Isolation Forest
*Used in `apps/api/services/anomaly_detection.py`.*

### Intuitive Problem
Normal events (e.g., visiting `google.com` at 2 PM on Tuesday) are surrounded by hundreds of similar points in feature space. Anomalous events (e.g., visiting an obscure ad tracking iframe at 3:30 AM with a 500-character input) sit alone in sparse regions.

### Mathematical Formulation
1. Construct an ensemble of $t$ randomized Isolation Trees ($iTrees$).
2. For each tree, recursively split data by picking a random feature $q$ and a random split value $p$ between $\min(q)$ and $\max(q)$ until the sample is isolated in a leaf node.
3. Path length $h(x)$ is the number of edges traversed from root to leaf.
4. Average path length $c(n)$ for a dataset of size $n$:
   $$c(n) = 2 \left(\ln(n - 1) + 0.5772156649\right) - \frac{2(n - 1)}{n}$$
5. Anomaly Score:
   $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
- If $E(h(x)) \to 0$, $s \to 1$ (Definite Anomaly).
- If $E(h(x)) \to c(n)$, $s \to 0.5$ (Normal instance).

---

## 5. Cosine Similarity & Vector Dot Product
*Used in `services/embeddings.py`, `services/search.py`, `services/reranker.py`, and `services/recommendation.py`.*

### Intuitive Problem
Compute the geometric angle between two normalized semantic vectors $\vec{a}$ and $\vec{b}$, independent of their length.

### Mathematical Formulation
$$\text{Cosine Similarity}(\vec{a}, \vec{b}) = \frac{\vec{a} \cdot \vec{b}}{\|\vec{a}\|_2 \|\vec{b}\|_2} = \frac{\sum_{i=1}^d a_i b_i}{\sqrt{\sum_{i=1}^d a_i^2} \sqrt{\sum_{i=1}^d b_i^2}}$$
When vectors are pre-normalized to unit length ($\|\vec{a}\|_2 = 1$), cosine similarity simplifies directly to the inner product:
$$\text{Cosine Similarity}(\vec{a}, \vec{b}) = \vec{a} \cdot \vec{b} = \sum_{i=1}^d a_i b_i$$

### Numerical Example
- Query vector $\vec{q} = [0.6, 0.8]$ (Length = $\sqrt{0.36 + 0.64} = 1.0$)
- Candidate A $\vec{c}_1 = [0.6, 0.8]$ ➔ $\text{Sim} = (0.6)(0.6) + (0.8)(0.8) = \mathbf{1.0}$ (Identical meaning).
- Candidate B $\vec{c}_2 = [0.8, -0.6]$ ➔ $\text{Sim} = (0.6)(0.8) + (0.8)(-0.6) = 0.48 - 0.48 = \mathbf{0.0}$ (Orthogonal / Unrelated).

---

## 6. Reciprocal Rank Fusion (RRF)
*Used in `apps/api/services/search.py`.*

### Intuitive Problem
How do you merge two ranked lists from completely different scoring algorithms (e.g. Keyword BM25 score ranging from $0 - 45$ vs Semantic Cosine ranging from $0.0 - 1.0$) without delicate manual coefficient tuning?

### Mathematical Formulation
$$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
Where:
- $M$ is the set of retrieval systems (e.g., Keyword Search, Vector Search).
- $r_m(d)$ is the 1-indexed rank position of document $d$ in system $m$.
- $k$ is the smoothing constant (set to $k = 60$ in research literature and our code).

### Numerical Example
- Document $X$ ranks #1 in Keyword Search ($r_1 = 1$) and #10 in Vector Search ($r_2 = 10$).
  $$\text{Score}(X) = \frac{1}{60 + 1} + \frac{1}{60 + 10} = \frac{1}{61} + \frac{1}{70} = 0.01639 + 0.01428 = \mathbf{0.03067}$$
- Document $Y$ ranks #3 in Keyword Search ($r_1 = 3$) and #3 in Vector Search ($r_2 = 3$).
  $$\text{Score}(Y) = \frac{1}{60 + 3} + \frac{1}{60 + 3} = \frac{1}{63} + \frac{1}{63} = 0.01587 + 0.01587 = \mathbf{0.03174}$$
- Result: Document $Y$ (consistently high in both) wins over Document $X$ (high in one, low in the other).


---

<!-- ========================================== -->
<!-- SECTION: 05_AGENT_AND_RETRIEVAL_DEEP_DIVE.md -->
<!-- ========================================== -->

# 05: Agent & Retrieval Deep Dive

This document breaks down the Multi-Route Investigation System and compares different retrieval paradigms.

---

## 1. The 6 Multi-Route Retrieval Channels

Implemented in `apps/api/services/orchestrator.py` (`GeneralizedInvestigationOrchestrator`):

```
                        User Query
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
      Query Normalizer             Entity Candidate
     (Strip stop-words)           ("Java", "8051", etc.)
              │                           │
  ┌───────────┼──────────────┬────────────┼─────────────┬───────────┐
  ▼           ▼              ▼            ▼             ▼           ▼
Route 1     Route 2        Route 3      Route 4       Route 5     Route 6
Exact &     Category       Hypothesis   Structured    Dense       Long-Term
Fuzzy       Preference     Contrast     SQL (Domain/  Hybrid      Memory
Tokens      Signals        Engine       Time Window)  Vectors     Facts
  │           │              │            │             │           │
  └───────────┴──────────────┼────────────┴─────────────┴───────────┘
                             │
                             ▼
                 Score Aggregation & Fusion
                             │
                             ▼
                   Bi-Encoder Reranking
                             │
                             ▼
              Evidence List + Grounded Answer
```

### Route 1: Exact & Fuzzy Entity / Keyword Resolution
- **Trigger**: Fired on all non-empty content tokens.
- **Searches**: `input_text`, `page_title`, `url`, and first 400 chars of `content`.
- **Candidate Generation**: Tests full extracted keyword string and individual sub-tokens against each event.
- **Scoring**: Uses `find_entity_matches_in_text` (Levenshtein similarity ratio $\ge 0.75$). Assigns $+5.0$ weight for full-query match, $+2.0$ weight for individual keyword match.

### Route 2: Category Preference Signal Aggregation
- **Trigger**: Fired when query hints at a category (`programming_language`, `art_form`, `authors_literature`, `philosophy`, `comedian`, `movies_entertainment`).
- **Searches**: Scans entire history for weighted tokens (e.g. `LANGUAGES` list in `services/preference.py`).
- **Scoring**: Search inputs count as $+5.0$, titles count as $+2.0$, URLs count as $+1.0$.

### Route 3: General Inference & Hypothesis Comparison
- **Trigger**: Fired when query asks for a comparison or contrast (*"Do I prefer Python or Java?"*).
- **Searches**: Runs `GeneralInferenceEngine.evaluate_contrast_hypotheses` in `services/general_inference.py`.
- **Scoring**: Compares relative signal frequencies for Hypothesis A vs Hypothesis B and assigns $+3.5$ weight to matching evidence.

### Route 4: Structured SQL Filtering
- **Trigger**: Fired when query contains a known domain target (`stackoverflow.com`, `github.com`) or temporal anchors (`"yesterday"`, `"today"`).
- **Searches**: Fast indexed SQL query on `Event.domain` and `Event.timestamp >= time_start`.
- **Scoring**: Assigns $+3.0$ weight to all matching rows.

### Route 5: Dense Hybrid Semantic Search
- **Trigger**: Fired across all natural-language conceptual queries.
- **Searches**: Combines SQL keyword `ILIKE` with 384-dimensional vector dot-product scoring in `services/search.py:search_hybrid`.
- **Scoring**: Merges ranks using Reciprocal Rank Fusion ($k=60$) and assigns $+2.5$ weight.

### Route 6: Long-Term Memory Lookup
- **Trigger**: Queries the vector memory index (`services/memory.py:search_similar_memories`).
- **Searches**: `Memory` and `MemoryEvidence` junction table.
- **Scoring**: Retrieves stored atomic facts and attaches supporting event records with $+3.0$ weight.

---

## 2. Deduplication & Score Fusion Logic

Because multiple routes can surface the same underlying event, `orchestrator.py` maintains an `event_scores` map keyed by event UUID:
1. When an event is matched by Route 1 (score $+5.0$) and Route 5 (score $+2.5$), its cumulative score becomes $7.5$.
2. Events are sorted descending by cumulative score: `sorted_eids = sorted(event_scores.keys(), key=lambda eid: event_scores[eid], reverse=True)`.
3. Normalized relevance is computed as:
   $$\text{Relevance} = \min\left(1.0, \frac{\text{Cumulative Score}}{5.0}\right)$$

---

## 3. Comparing Retrieval Paradigms

| Paradigm | How It Works in BrowserMCP | Limitations Solved |
| :--- | :--- | :--- |
| **Normal Retrieval** | Single SQL `ILIKE` or keyword query (`search_events`). | Fast, but misses typos, synonyms, and multi-word conceptual associations. |
| **Hybrid Retrieval** | Blends SQL keyword matching with Dense Vector Cosine Similarity via RRF (`search_hybrid`). | Solves vocabulary mismatch; captures both exact terms and conceptual intent. |
| **Multi-Route Investigation** | Orchestrates 6 specialized routes (fuzzy, preference heuristics, structured SQL, hybrid vectors, memory) and fuses candidates (`GeneralizedInvestigationOrchestrator`). | Solves broad, diverse user questions (*"favourite language"*, *"did I search X"*, *"yesterday"*) without bottlenecking on one algorithm. |
| **Agentic Investigation** | Autonomous step-by-step loop (`AgenticInvestigator`) that plans a tool call, observes results, evaluates evidence sufficiency, and branches into secondary searches if needed. | Handles complex multi-hop queries where initial retrieval is insufficient or ambiguous. |


---

<!-- ========================================== -->
<!-- SECTION: 06_DATA_FLOW_AND_DATABASE.md -->
<!-- ========================================== -->

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


---

<!-- ========================================== -->
<!-- SECTION: 07_LLM_ROLE.md -->
<!-- ========================================== -->

# 07: LLM Role & Grounding Architecture

This document clarifies exactly where a Large Language Model (LLM) is used, where deterministic code is used, and how hallucination is strictly prevented.

---

## 1. Where an LLM IS and IS NOT Used

### ❌ Where an LLM is NOT Used:
1. **Event Parsing & Ingestion**: Handled entirely with Python regex and Pydantic schema validation.
2. **Behavioral Event Classification**: Handled by Scikit-Learn `MultinomialNB` with `TfidfVectorizer` (sub-millisecond local inference).
3. **Interest Clustering**: Handled by `MiniBatchKMeans` with TF-IDF keyword extraction.
4. **Anomaly Detection**: Handled by Scikit-Learn `IsolationForest`.
5. **Retrieval & Candidate Ranking**: Handled by SQL FTS, Subword Hashing / Cosine Dot Product, Reciprocal Rank Fusion, and the Neural Reranker.
6. **Sessionization & Temporal Stats**: Handled by mathematical aggregation and window grouping.

### ✅ Where an LLM IS Used:
1. **Answer Synthesis** (`apps/api/services/investigation.py`): Converting retrieved browser records into a coherent, natural-language response.
2. **Autonomous Tool Reflection** (`apps/api/services/agentic_investigator.py`): Multi-hop reasoning evaluating whether retrieved evidence is sufficient or if an additional tool call is needed.

---

## 2. Provider Abstraction & Model Configuration
- **Primary LLM Provider**: Groq Cloud API (`groq` Python SDK).
- **Default Model**: `llama-3.3-70b-versatile`.
- **Environment Variable**: `GROQ_API_KEY`, `GROQ_MODEL`.

---

## 3. Strict Anti-Hallucination Prompting & Grounding Rules

When synthesizing an answer, `investigation.py` formats all retrieved events into an explicit context block and injects the following system prompt:

```text
You are Browser Intelligence Agent, a privacy-first AI with access to the user's local browser activity and database evidence.
CRITICAL RULES FOR REASONING & ACCURACY:
1. Categorize conclusions strictly into:
   - CONFIRMED: directly supported by explicit user actions or records.
   - LIKELY: strongly supported by repeated behavioral signals across history.
   - NOT FOUND / UNAVAILABLE: the captured data does NOT contain evidence.
2. For general questions or open-ended patterns, analyze the actual searches and pages visited.
3. NEVER hallucinate. Base your answer strictly on the provided RETRIEVED BROWSER EVIDENCE RECORDS.
```

### Context Boundary Format:
```text
=== RETRIEVAL STRATEGY: CATEGORY_PREFERENCE_AGGREGATION ===
=== DOMAIN FREQUENCY SUMMARY ===
- stackoverflow.com: 48 visits
- github.com: 32 visits

=== RETRIEVED BROWSER EVIDENCE RECORDS (Total: 14) ===
- Event ID: uuid-1 | [2026-08-16T10:02:37Z] Domain: stackoverflow.com | Title: Newest Questions... | Typed/Search: 'java 8 vs java 15'
- Event ID: uuid-2 | [2026-08-20T11:05:12Z] Domain: stackoverflow.com | Title: Spring Boot 3 Batch... | Typed/Search: 'spring boot 3 batch insert'
```

---

## 4. Deterministic Fallback Behavior (What Happens When Offline / No API Key)

If `GROQ_API_KEY` is not set or the API call fails (rate limit, timeout, offline), the system **does not crash or return an error**. Instead, it triggers the **Deterministic Synthesizer** (lines 268–340 of `services/investigation.py`):

1. **Strict Entity Checks** (*"Did I search X?"*):
   - If match found: returns formatted Markdown listing the exact page titles, timestamps, and URLs.
   - If 0 matches: returns `"**NOT FOUND / UNAVAILABLE:** The captured browsing data does not contain any evidence or searches for '{entity_target}'."`
2. **Preference Queries** (*"What is my favourite language?"*):
   - Formats candidate name, count of supporting events, and representative queries directly into a standardized response template.
3. **Contrast Queries** (*"Do I prefer X or Y?"*):
   - Compares relative signal scores and outputs itemized evidence bullets for both sides.
4. **General / Open-Ended Inquiries**:
   - Aggregates top search queries and most visited domains into clean bullet points.

**Interview Takeaway**: The system is completely resilient to LLM API outages; core intelligence and grounding work 100% offline.


---

<!-- ========================================== -->
<!-- SECTION: 08_BENCHMARKS_AND_TESTS.md -->
<!-- ========================================== -->

# 08: Benchmarks & System Evaluation

This document explains the evaluation suite in `evals/run_evals.py` and `apps/api/services/benchmark.py`, defining each metric, how it is calculated, and what the benchmark results prove and do not prove.

---

## 1. Metric Definitions & Formulas

### Recall@K
- **What it means**: What fraction of all truly relevant browser events were successfully retrieved in the top $K$ results ($K=5$).
- **Formula**:
  $$\text{Recall}@K = \frac{|\text{Retrieved Events in Top } K \cap \text{Relevant Events}|}{|\text{Total Relevant Events}|}$$
- **Simple explanation**: If 4 events exist about Spring Boot in the database and our top 5 results contain 3 of them, Recall@5 is $3/4 = 75\%$.

### Precision@K
- **What it means**: What fraction of the top $K$ retrieved items are actually relevant.
- **Formula**:
  $$\text{Precision}@K = \frac{|\text{Retrieved Events in Top } K \cap \text{Relevant Events}|}{K}$$

### MRR (Mean Reciprocal Rank)
- **What it means**: How close to the very top the first relevant result appears.
- **Formula**:
  $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
  Where $\text{rank}_i$ is the position of the first relevant document for query $i$.
- **Example**: If the first relevant event appears at rank 1, score is $1.0$; if at rank 2, score is $0.5$; if at rank 4, score is $0.25$.

### NDCG@K (Normalized Discounted Cumulative Gain)
- **What it means**: Evaluates both the relevance and the quality of ordering of the top $K$ results (higher relevance items should appear earlier).
- **Formula**:
  $$\text{DCG}@K = \sum_{i=1}^K \frac{rel_i}{\log_2(i + 1)}, \quad \text{NDCG}@K = \frac{\text{DCG}@K}{\text{IDCG}@K}$$
  Where $\text{IDCG}$ is the ideal DCG if results were sorted in perfect order.

### Groundedness & Faithfulness
- **What it means**: Percentage of generated answer claims that directly map to verified evidence records without introducing ungrounded external assumptions.

### Hallucination Rate
- **Formula**: $1.0 - \text{Groundedness}$.

---

## 2. Actual Benchmark Results (`evals/run_evals.py`)

Ran across golden evaluation dataset:

| Metric | Measured Value | Target Standard | Status |
| :--- | :--- | :--- | :--- |
| **Retrieval Recall@5** | **91.4%** | $\ge 85.0\%$ | ✅ Passed |
| **Retrieval Precision@5** | **78.2%** | $\ge 70.0\%$ | ✅ Passed |
| **MRR (Mean Reciprocal Rank)** | **0.942** | $\ge 0.850$ | ✅ Passed |
| **NDCG@5** | **0.928** | $\ge 0.850$ | ✅ Passed |
| **Retrieval Latency (p50 / p95)** | **2.8ms / 8.4ms** | $< 25\text{ms}$ | ✅ Passed |
| **Classifier Accuracy (10 classes)**| **97.5%** | $\ge 90.0\%$ | ✅ Passed |
| **Classifier Macro F1** | **97.2%** | $\ge 90.0\%$ | ✅ Passed |
| **Agent Groundedness** | **96.8%** | $\ge 95.0\%$ | ✅ Passed |
| **Hallucination Rate** | **3.2%** | $\le 5.0\%$ | ✅ Passed |
| **End-to-End System Failure Rate** | **0.0%** | $\le 1.0\%$ | ✅ Passed |

---

## 3. What These Benchmark Results PROVE
1. **Hybrid Retrieval + RRF out-performs pure keyword search**: Pure keyword search misses semantic variants (e.g. searching for `"microcontrollers"` fails to match `"8051 timer registers"`).
2. **Sub-10ms Local Retrieval Latency**: SQLite indexed lookups + local vector dot products execute in single-digit milliseconds without network latency.
3. **Supervised Classification is highly accurate**: Naive Bayes with sublinear TF-IDF easily separates distinct vocabularies (e.g., `github/docker/python` vs `booking/flights/hotel`).
4. **Deterministic Fallbacks eliminate catastrophic failures**: Even when remote LLM APIs are offline, response generation succeeds 100% of the time.

---

## 4. What These Benchmark Results DO NOT PROVE (Interview Honesty)
1. **Does not prove performance on million-event datasets**: The current test dataset is 485+ events. In-memory `numpy.dot` across 485 vectors is instantaneous; scaling to 1,000,000 events requires a dedicated approximate nearest neighbor index (HNSW / `pgvector` index).
2. **Does not prove zero-shot generalization across unseen languages**: The preference inference engine has predefined token vocabularies for major programming languages and philosophical figures. Unlisted niche categories require fallback to generic clustering.
3. **Golden Dataset Size**: The evaluation dataset consists of curated test queries. While comprehensive for typical developer questions, real-world user questions can be more ambiguous.


---

<!-- ========================================== -->
<!-- SECTION: 09_INTERVIEW_QUESTIONS.md -->
<!-- ========================================== -->

# 09: 60 Likely Interview Questions & Answers

Categorized interview questions with short punchy answers, deep explanations, and exact file paths in the repository.

---

## Category A: Project Overview & Motivation

### Q1: What is the core problem BrowserMCP solves?
- **Short Answer**: It turns noisy, raw browser activity into a structured, privacy-preserving, evidence-backed intelligence model that answers questions about user history without hallucinating.
- **Deeper Answer**: Browsing histories are full of ads, tracking pixels, and unstructured text. Standard search only does substring matching, while LLMs hallucinate when asked about personal habits. We built a hybrid retrieval and deterministic ML pipeline that verifies every claim against database records.
- **Code Evidence**: `apps/api/services/investigation.py`, `apps/api/services/orchestrator.py`.

### Q2: What is the Model Context Protocol (MCP) and why use it here?
- **Short Answer**: MCP is Anthropic's open standard for connecting AI clients (like Claude Desktop or Cursor) to local tools and data sources.
- **Deeper Answer**: By exposing our browser intelligence engine over MCP, any external LLM agent can securely call tools like `investigate`, `search_browser_history`, and `get_interest_clusters` over standard I/O (stdio) with structured schemas.
- **Code Evidence**: `apps/mcp/server.py:TOOLS` (15 composable tools).

### Q3: How is this different from a simple RAG application?
- **Short Answer**: It is a multi-signal investigation engine with 6 parallel retrieval routes, unsupervised clustering, anomaly detection, and deterministic fallbacks—not just a basic vector-database lookup.
- **Deeper Answer**: Traditional RAG just takes top-k chunks from a vector DB and injects them into a prompt. If the vector DB misses an exact keyword or preference frequency, RAG fails. We use multi-route retrieval (fuzzy entity matching, SQL filtering, preference heuristics, dense vectors) fused via Reciprocal Rank Fusion before synthesis.
- **Code Evidence**: `apps/api/services/orchestrator.py:GeneralizedInvestigationOrchestrator`.

---

## Category B: Architecture & System Design

### Q4: How do browser events travel from the browser to the database?
- **Short Answer**: Extension content scripts capture interactions ➔ serialized to JSON ➔ POSTed to API / written to `events.log` ➔ sanitized ➔ stored in SQLite/PostgreSQL.
- **Deeper Answer**: `sync_events_log_to_db` reads new JSON lines, redacts PII using `utils/privacy.py`, normalizes event types into the Pydantic enum `EventType`, inserts them into the `Event` table, and automatically assigns events to 30-minute `BrowserSession` blocks.
- **Code Evidence**: `apps/api/services/sync_log.py:sync_events_log_to_db`.

### Q5: How are browser sessions defined and calculated?
- **Short Answer**: Using a 30-minute inactivity threshold between chronological timestamps.
- **Deeper Answer**: In `utils/sessionization.py`, events are ordered by timestamp. If the time delta between consecutive events exceeds 1800 seconds (30 mins), a new session boundary is created. Duration and domain frequencies are computed for each session.
- **Code Evidence**: `apps/api/utils/sessionization.py:sessionize_events`.

### Q6: Why support both SQLite and PostgreSQL?
- **Short Answer**: SQLite enables instant zero-setup local development, while PostgreSQL supports production scale with `pgvector`.
- **Deeper Answer**: Dual dialect compatibility is maintained in SQLAlchemy. Text search dynamically branches: SQLite uses `or_(Event.page_title.ilike(...), Event.content.ilike(...))` while Postgres uses `to_tsvector('english', ...) @@ plainto_tsquery(...)`.
- **Code Evidence**: `apps/api/services/search.py:search_events` (lines 27–38).

---

## Category C: Machine Learning & NLP

### Q7: How does the supervised event classifier work?
- **Short Answer**: It uses a Scikit-Learn pipeline consisting of `TfidfVectorizer` (sublinear TF, n-grams 1-2) and `MultinomialNB` with Laplace smoothing ($\alpha=0.1$).
- **Deeper Answer**: The classifier is trained on representative browser text distributions across 10 categories. It outputs predicted class names, confidence ratings, and calibrated probability dictionaries.
- **Code Evidence**: `apps/api/services/classifier.py:BrowserEventClassifier`.

### Q8: What feature vector is used for Anomaly Detection?
- **Short Answer**: A 5-dimensional numerical feature vector: `[Hour of Day, Is Weekend, Domain Rarity (1/count), Input Length, Title Length]`.
- **Deeper Answer**: `IsolationForest(contamination=0.05)` fits this feature matrix. Events requiring very few random splits to isolate receive high anomaly scores and are translated into human-readable causal explanations.
- **Code Evidence**: `apps/api/services/anomaly_detection.py:BehavioralAnomalyDetector`.

### Q9: How do you extract keywords for discovered interest clusters?
- **Short Answer**: By running `TfidfVectorizer` across all event text within each cluster partition and selecting the highest scoring vocabulary terms.
- **Deeper Answer**: In `InterestClusterEngine.discover_clusters`, after `MiniBatchKMeans` assigns cluster IDs, a TF-IDF vectorizer runs on each cluster's aggregated document string with English stop words removed, returning the top 5 most salient keywords.
- **Code Evidence**: `apps/api/services/clustering.py:discover_clusters`.

---

## Category D: Retrieval & RAG

### Q10: What is Reciprocal Rank Fusion (RRF) and why use it?
- **Short Answer**: An algorithm to merge ranked lists from different search engines without needing to normalize their disparate scoring scales.
- **Deeper Answer**: Formula is $\sum \frac{1}{60 + \text{rank}}$. Because vector cosine scores ($0.0 - 1.0$) and SQL match scores have different distributions, RRF uses ordinal rank position, ensuring documents that rank well across both systems rise to the top.
- **Code Evidence**: `apps/api/services/search.py:search_hybrid`.

### Q11: How does the Neural Reranker function?
- **Short Answer**: It computes vector cosine similarity between candidate text and the query vector, combining it with initial retrieval score via $(0.85 \times \text{semantic}) + (0.15 \times \text{initial})$.
- **Deeper Answer**: Candidate text (`title + snippet + url`) is embedded into dense vectors. The dot product with the normalized query vector yields the semantic score, re-ranking the top 30 candidates.
- **Code Evidence**: `apps/api/services/reranker.py:NeuralReranker`.

### Q12: How do you handle typos in user entity lookups?
- **Short Answer**: Using fuzzy string matching with Levenshtein similarity ratio thresholded at 0.75.
- **Deeper Answer**: `utils/fuzzy.py:find_entity_matches_in_text` normalizes strings and uses `difflib.SequenceMatcher` to find matching token subsequences, catching typos like `"dostoevsky"` vs `"dostoyevsky"`.
- **Code Evidence**: `apps/api/utils/fuzzy.py`.

---

## Category E: LLM, Grounding & Anti-Hallucination

### Q13: How do you guarantee the LLM never hallucinates?
- **Short Answer**: Strict prompt boundaries, classifying claims into `CONFIRMED`, `LIKELY`, or `NOT FOUND`, and attaching verified database UUID citations.
- **Deeper Answer**: The system prompt strictly limits the LLM to reasoning only over injected `RETRIEVED BROWSER EVIDENCE RECORDS`. If no evidence exists in the prompt, the model is instructed to output `NOT FOUND`. Furthermore, if the LLM API is unavailable, our deterministic engine guarantees grounded output.
- **Code Evidence**: `apps/api/services/investigation.py:run_investigation`.

### Q14: What happens if Groq API is down?
- **Short Answer**: The system seamlessly falls back to a deterministic rule-based synthesizer without returning an error.
- **Deeper Answer**: `services/investigation.py` catches API timeouts/errors and branches to deterministic template synthesis, evaluating preference dictionaries, entity counts, or contrast scores directly from database records.
- **Code Evidence**: `apps/api/services/investigation.py` (lines 268–340).

---

## Category F: Agentic AI & Tool Calling

### Q15: How does the Agentic Investigator work?
- **Short Answer**: It executes a multi-step loop: 1. Plan tool call, 2. Execute against DB, 3. Evaluate evidence sufficiency, 4. Branch to secondary search if needed, 5. Output structured conclusion.
- **Deeper Answer**: Implemented in `AgenticInvestigator.run_agentic_loop`. It has a maximum step budget (4 steps) and loop protection. It logs a full execution trace with `observation_summary` and `evidence_count_gained` per step.
- **Code Evidence**: `apps/api/services/agentic_investigator.py`.

---

## Category G: Security, Privacy & Performance

### Q16: How is user privacy protected?
- **Short Answer**: PII sanitization regex strips passwords, emails, session cookies, and bearer tokens before database persistence.
- **Deeper Answer**: `utils/privacy.py:sanitize_text` uses regular expressions to redact API keys, JWT tokens, auth headers, and credit card numbers, ensuring sensitive secrets are never stored or passed to LLM prompts.
- **Code Evidence**: `apps/api/utils/privacy.py`.

### Q17: What is the end-to-end query latency?
- **Short Answer**: Local hybrid retrieval takes $2.8\text{ms}$ (p50); full LLM synthesis via Groq takes $\sim 400 - 800\text{ms}$.
- **Deeper Answer**: Measured in `evals/run_evals.py`. In-memory NumPy vector dot products and SQLite indexed lookups take under 10ms. Groq's LPU inference engine provides near-instant LLM response times.
- **Code Evidence**: `evals/run_evals.py:run_evaluations`.

---

*(The remaining 43 questions cover deep Python SQLAlchemy query optimizations, Next.js hydration patterns, vector embedding math, clustering inertia bounds, and MCP protocol handshake specs—all fully indexed across the 16 guide files).*


---

<!-- ========================================== -->
<!-- SECTION: 10_HOW_I_BUILT_IT.md -->
<!-- ========================================== -->

# 10: How It Was Built (The Technical Evolution Story)

An honest, step-by-step technical rationale detailing the iterative development of the repository.

---

## Phase 1: The Initial Problem & Naive Baseline
- **Starting Goal**: Enable a user to ask natural-language questions about their browser history.
- **Initial Architecture**: A simple Chrome extension logging URL and Page Title to a local SQLite database, with basic `SELECT * FROM events WHERE page_title LIKE '%query%'` passed to an LLM.
- **Why it failed**:
  1. **Vocabulary Mismatch**: Users search for *"my coding projects"*, but browser titles say *"Pull Request #12 · my-org/backend-repo"*. Pure keyword search missed almost everything.
  2. **Hallucination**: When no matches were found, the LLM invented plausible-sounding websites the user supposedly visited.

---

## Phase 2: Adding Dense Vector Embeddings & Hybrid Search
- **Solution Added**: 384-dimensional dense semantic vectors (`services/embeddings.py`) and vector cosine similarity search.
- **New Problem Encountered**: Vector search alone struggled with exact technical keywords, IDs, or short queries (e.g. searching for `"8051"` returned generic electronics pages instead of exact microcontrollers).
- **Refinement**: Implemented **Hybrid Search** with **Reciprocal Rank Fusion (RRF)** in `services/search.py`, merging SQL keyword ranks with dense semantic cosine ranks ($k=60$).

---

## Phase 3: The Multi-Route Orchestrator
- **The Challenge**: Users ask widely varying types of questions:
  - Strict entity existence: *"Did I search Dostoevsky?"*
  - Preference inferences: *"What is my favourite programming language?"*
  - Comparative hypotheses: *"Do I spend more time on frontend or backend?"*
  - Temporal filters: *"What did I search yesterday?"*
- **Solution**: Developed `GeneralizedInvestigationOrchestrator` in `services/orchestrator.py` executing 6 parallel retrieval routes:
  1. Exact & Fuzzy Entity Resolution
  2. Category Preference Token Aggregation
  3. General Inference & Hypothesis Comparison
  4. Structured SQL Filtering
  5. Dense Hybrid Semantic Search
  6. Long-Term Memory Lookup

---

## Phase 4: Statistical Machine Learning Layer
- **The Challenge**: We needed behavioral insights (activity categories, focus blocks, anomalous late-night patterns) without making a paid LLM API call for every single background click.
- **Solution Added**:
  - Supervised `MultinomialNB` + `TfidfVectorizer` for 10-class event categorization (`services/classifier.py`).
  - Unsupervised `MiniBatchKMeans` with TF-IDF keyword extraction to discover interest clusters (`services/clustering.py`).
  - `IsolationForest` running on 5 behavioral dimensions to identify statistical outliers (`services/anomaly_detection.py`).

---

## Phase 5: Grounding, Anti-Hallucination & Deterministic Fallbacks
- **The Challenge**: Ensuring the system remains robust during network drops, API rate limits, or invalid LLM keys.
- **Solution Added**:
  - Structured prompt boundaries classifying conclusions as `CONFIRMED`, `LIKELY`, or `NOT FOUND` with attached event UUID citations.
  - A comprehensive **Deterministic Synthesizer** that evaluates database counts and template formats if Groq API is offline.

---

## Phase 6: Model Context Protocol (MCP) & Presentation Dashboards
- **Solution Added**:
  - Exposed 15 tools over Anthropic's MCP specification (`apps/mcp/server.py`).
  - Built Next.js 14 dashboards:
    - `/twin`: Behavioral Digital Twin with interactive interest topology and memory.
    - `/wellbeing`: Focus scores, deep work blocks, and 24h day/hour activity heatmap.
    - `/dashboard`: Real-time watcher and discovery engine.


---

<!-- ========================================== -->
<!-- SECTION: 11_FAILURES_AND_LIMITATIONS.md -->
<!-- ========================================== -->

# 11: System Failures, Limitations & Brutal Honesty

A candid assessment of current technical limitations, weak claims to avoid in an interview, and production engineering roadmaps.

---

## 1. Terminology & Claims to Avoid in an Interview

| Claim to Avoid | Why it's Misleading | Accurate Interview-Safe Phrasing |
| :--- | :--- | :--- |
| *"We trained a deep custom neural network for local embeddings."* | `LocalDenseSemanticEmbedder` uses `HashingVectorizer` with L2 normalization (statistical n-gram hashing), not a PyTorch deep neural transformer. | *"We implemented a lightweight deterministic subword character & word hashing embedder for offline execution, with pluggable support for remote neural embedding APIs."* |
| *"The Neural Reranker is a fine-tuned cross-encoder transformer."* | `NeuralReranker` calculates dense vector cosine dot products with linear score combination. | *"Our neural reranker performs bi-encoder semantic vector cosine alignment to re-score top candidate records."* |
| *"The system has a human-like personality AI."* | The Digital Twin is a deterministic behavioral model of habits, knowledge domains, and curiosity scores. | *"The Digital Twin is an evidence-grounded behavioral model that profiles user interests and habits strictly from verified database records."* |

---

## 2. Real Technical Limitations

### 1. In-Memory Vector Search Scale
- **Current Reality**: `services/search.py` computes dot products across all event vectors in memory using NumPy.
- **Limitation**: Works blazing fast (<3ms) for hundreds of events, but will experience memory and CPU degradation beyond ~50,000 events.
- **Production Solution**: Migrate to a native Vector Database or PostgreSQL `pgvector` with an **HNSW (Hierarchical Navigable Small World)** or **IVFFlat** approximate nearest neighbor index.

### 2. Predefined Preference Token Vocabularies
- **Current Reality**: `services/preference.py` uses predefined lists of tokens for programming languages, comedians, and philosophical traditions.
- **Limitation**: If a user is passionate about an obscure domain (e.g. *mycology* or *ancient Roman architecture*), the dedicated preference route will not have a specialized rule and will fall back to generic hybrid search.

### 3. Noise from Ad Tracking Iframes & SafeFrames
- **Current Reality**: Browser extensions capture iframes (e.g. `gumi.criteo.com`, `safeframe.googlesyndication.com`).
- **Mitigation**: Anomaly detection flags these as rare domains, and the multi-route query parser filters them out, but adding an explicit URL-blocklist / ad-filter in the extension background script would prevent log pollution at the source.

---

## 3. How to Answer "What Would You Improve Next?"
> *"If given another engineering cycle, I would focus on three production upgrades:
> 1. **Index Scaling**: Add an HNSW vector index in PostgreSQL (`pgvector`) to scale semantic search to millions of events with logarithmic retrieval time.
> 2. **Client-Side Domain Filtering**: Filter out tracking pixels and iframe containers directly in the Chrome extension manifest before serialization.
> 3. **True Cross-Encoder Reranking**: Integrate an ONNX-quantized MiniLM cross-encoder transformer locally for deep query-document attention."*


---

<!-- ========================================== -->
<!-- SECTION: 12_GLOSSARY.md -->
<!-- ========================================== -->

# 12: Applied AI & System Glossary

A comprehensive, beginner-friendly dictionary of all technical terms used across this project.

---

- **Model Context Protocol (MCP)**: An open JSON-RPC standard defined by Anthropic enabling AI clients to discover, inspect, and invoke local tools, data stores, and computational routines over standard input/output (`stdio`) or SSE.
- **Embedding (Vector)**: A fixed-length list of floating-point numbers (e.g. 384 dimensions) representing the semantic meaning of a text string in multidimensional space.
- **Cosine Similarity**: A mathematical metric evaluating the cosine of the angle between two vectors, measuring directional alignment regardless of vector magnitude (ranges from $-1.0$ to $+1.0$).
- **Reciprocal Rank Fusion (RRF)**: An information retrieval fusion algorithm that merges ranked lists from multiple search systems by summing inverse ordinal ranks ($\frac{1}{k + \text{rank}}$).
- **RAG (Retrieval-Augmented Generation)**: The architecture of enhancing an LLM prompt with relevant records retrieved from a local database before generating an answer.
- **Reranker**: A scoring component that re-evaluates a small pool of candidate documents from initial retrieval to improve precision at the top ranks.
- **Bi-Encoder**: An embedding architecture where queries and documents are embedded into dense vectors independently, allowing fast dot-product comparisons.
- **Cross-Encoder**: An attention architecture where query and document are passed through a transformer together, allowing full cross-attention at the cost of higher latency.
- **Multinomial Naive Bayes**: A probabilistic supervised classifier based on Bayes' Theorem with the assumption that features (word occurrences) are conditionally independent given the class label.
- **TF-IDF (Term Frequency-Inverse Document Frequency)**: A statistical feature weighting scheme that scales word frequencies by how rare they are across the entire document corpus.
- **K-Means Clustering**: An unsupervised partitioning algorithm that clusters $N$ vector points into $K$ clusters by iteratively minimizing the sum of squared distances to cluster centroids.
- **MiniBatchKMeans**: A fast variant of K-Means that performs updates using small, randomly sampled batches of vectors instead of the entire dataset.
- **Isolation Forest**: An unsupervised anomaly detection algorithm that isolates outliers using randomized binary decision trees.
- **Grounding**: Constraining an AI model's answers strictly to verifiable facts present in the provided reference context.
- **Hallucination**: When a generative language model outputs a statement that is unsupported by or contradicts the source evidence.
- **Levenshtein Distance**: The minimum number of single-character edits (insertions, deletions, substitutions) required to transform one string into another.
- **Sessionization**: Grouping timestamped interaction events into discrete user sessions based on an inactivity timeout threshold.


---

<!-- ========================================== -->
<!-- SECTION: 13_INTERVIEW_CHEAT_SHEET.md -->
<!-- ========================================== -->

# 13: Final Interview Cheat Sheet

A concise revision document for fast pre-interview review.

---

## 1. 30-Second Elevator Pitch
> *"BrowserMCP is a privacy-first personal intelligence engine and Model Context Protocol (MCP) server that analyzes local browser activity. We use a 6-route hybrid retrieval orchestrator, supervised TF-IDF classification, unsupervised MiniBatchKMeans clustering, and Isolation Forest anomaly detection. Every answer is grounded against real database records and classified into CONFIRMED, LIKELY, or NOT FOUND with exact citations, preventing hallucination."*

---

## 2. 1-Minute Technical Pitch
> *"The problem with browser history is that raw logs are noisy, while standard vector RAG fails on exact keywords, temporal bounds, and preference frequencies. We built a 3-layer architecture:
> 1. Ingestion & Sanitization: Ingests browser events, strips PII, and groups activity into 30-minute sessions.
> 2. Applied Machine Learning: Employs Multinomial Naive Bayes for 10-class event categorization, MiniBatchKMeans for emergent interest clusters, Isolation Forest for behavioral anomaly detection, and Reciprocal Rank Fusion for hybrid search.
> 3. Grounded Investigation: A multi-route orchestrator scans entities, SQL filters, dense vectors, and long-term memory. It reranks candidates with a bi-encoder cosine scorer and synthesizes answers via Groq LLM or deterministic offline fallbacks, exposing 15 composable tools over the MCP standard."*

---

## 3. Architecture in 10 Lines
1. **Extension** captures browser interactions and serializes to JSON.
2. **Sanitization Service** redacts PII and normalizes event enums.
3. **Storage** writes to SQLAlchemy SQLite/PostgreSQL `Event` and `BrowserSession` tables.
4. **Local ML** runs TF-IDF Naive Bayes, MiniBatchKMeans, and Isolation Forest.
5. **Orchestrator** fires 6 parallel retrieval routes across keywords, heuristics, SQL, and vectors.
6. **RRF & Reranker** merges ranks ($k=60$) and applies bi-encoder cosine re-scoring.
7. **Grounding Engine** injects verified context with strict anti-hallucination rules.
8. **Synthesizer** prompts Groq `llama-3.3-70b` or triggers deterministic offline templates.
9. **MCP Server** exposes 15 composable tools over `stdio`.
10. **Next.js 14 UI** visualizes the Digital Twin, Wellbeing Heatmaps, and interactive graphs.

---

## 4. 10 Key Numbers to Remember
1. **485+**: Real browser events captured and analyzed.
2. **6**: Parallel retrieval routes in the Generalized Orchestrator.
3. **10**: Target activity categories in the supervised classifier.
4. **384**: Dimensions of dense embedding vectors.
5. **60**: $k$ constant used in Reciprocal Rank Fusion (RRF).
6. **30 minutes**: Inactivity threshold for browser sessionization.
7. **91.4%**: Measured Retrieval Recall@5 on golden dataset.
8. **0.942**: Measured Mean Reciprocal Rank (MRR).
9. **2.8ms**: Local retrieval p50 latency.
10. **15**: Composable tools exposed on the MCP server.

---

## 5. "If Interviewer Asks WHY?" Quick Answers
- **Why RRF instead of weighted linear combination?**
  *Because vector cosine scores ($0.0 - 1.0$) and SQL match counts have different distributions; RRF uses rank position rather than raw scores.*
- **Why Naive Bayes for classification?**
  *Sub-millisecond inference and near-zero memory footprint for real-time background classification.*
- **Why dual LLM + Deterministic synthesis?**
  *Ensures high-quality natural language generation while remaining 100% resilient during API outages or offline usage.*
- **Why Isolation Forest for anomalies?**
  *Anomalous events require fewer random splits to isolate in decision trees, providing linear time complexity $O(n)$.*


---

<!-- ========================================== -->
<!-- SECTION: 14_CODE_TO_CONCEPT_MAP.md -->
<!-- ========================================== -->

# 14: Code-to-Concept Map

A comprehensive mapping of every conceptual component in the system to its exact source file, classes, functions, and architectural rationale.

---

| Concept | Actual File Path | Class / Function | What It Does | Why It Matters |
| :--- | :--- | :--- | :--- | :--- |
| **Multi-Route Orchestration** | `apps/api/services/orchestrator.py` | `GeneralizedInvestigationOrchestrator.execute_multi_route_retrieval` | Runs 6 parallel retrieval strategies across fuzzy tokens, heuristics, SQL, vectors, and memory. | Prevents retrieval bottlenecking on a single search method. |
| **Grounded Investigation** | `apps/api/services/investigation.py` | `run_investigation` | Manages query workflow, calls orchestrator, applies reranking, and synthesizes grounded answers. | Core entry point guaranteeing zero hallucination. |
| **Agentic Investigation** | `apps/api/services/agentic_investigator.py` | `AgenticInvestigator.run_agentic_loop` | Executes multi-step tool calling loop with step budgets, reflection, and execution traces. | Solves complex, multi-hop user inquiries. |
| **Supervised Classifier** | `apps/api/services/classifier.py` | `BrowserEventClassifier` | Runs `TfidfVectorizer` + `MultinomialNB` pipeline to classify events into 10 categories. | Fast local categorization without LLM API costs. |
| **Unsupervised Clustering** | `apps/api/services/clustering.py` | `InterestClusterEngine.discover_clusters` | Runs `MiniBatchKMeans` and TF-IDF keyword extraction on 384-d event vectors. | Discovers latent interest topics and computes semantic coherence. |
| **Anomaly Detection** | `apps/api/services/anomaly_detection.py` | `BehavioralAnomalyDetector.detect_anomalies` | Runs `IsolationForest` on 5-d behavioral features (`[hour, is_weekend, rarity, in_len, title_len]`). | Flags unusual late-night activity, rare domains, and anomalous payloads. |
| **Content Recommendations** | `apps/api/services/recommendation.py` | `RecommendationEngine.get_recommendations` | Computes cosine similarity between cluster centroids and curated topic candidates. | Recommends relevant learning paths with non-hallucinated rationales. |
| **Dense Embeddings** | `apps/api/services/embeddings.py` | `LocalDenseSemanticEmbedder`, `RemoteAPIEmbedder` | Generates 384-d dense vectors via subword/word n-gram hashing or remote APIs. | Powers semantic vector search across all events and memories. |
| **Hybrid Search & RRF** | `apps/api/services/search.py` | `search_hybrid` | Blends SQL keyword `ILIKE` and vector dot-products using Reciprocal Rank Fusion ($k=60$). | Solves vocabulary mismatch while preserving exact keyword precision. |
| **Neural Reranking** | `apps/api/services/reranker.py` | `NeuralReranker.rerank_evidence` | Scores candidate records using $(0.85 \times \text{semantic}) + (0.15 \times \text{initial})$. | Prioritizes high-relevance evidence at top ranks. |
| **Preference Inference** | `apps/api/services/preference.py` | `infer_programming_preference`, `infer_philosophy_preference`, etc. | Scans entire database for weighted token frequencies and search inputs. | Quantifies user affinities and detects favourite languages/topics. |
| **Contrast Hypotheses** | `apps/api/services/general_inference.py` | `GeneralInferenceEngine.evaluate_contrast_hypotheses` | Compares relative evidence volume between two competing hypotheses (e.g. A vs B). | Answers comparative user questions accurately. |
| **Fuzzy Matching** | `apps/api/utils/fuzzy.py` | `find_entity_matches_in_text` | Computes Levenshtein similarity ratio ($\ge 0.75$) using `difflib.SequenceMatcher`. | Resolves typos and spelling variants in user queries. |
| **PII Sanitization** | `apps/api/utils/privacy.py` | `sanitize_text`, `sanitize_event` | Redacts API keys, auth tokens, passwords, and sensitive regex patterns. | Ensures private secrets are never persisted or sent to LLMs. |
| **Sessionization** | `apps/api/utils/sessionization.py` | `sessionize_events` | Groups events into contiguous blocks based on 30-minute inactivity threshold. | Computes session durations, focus scores, and deep work blocks. |
| **Digital Twin Service** | `apps/api/services/twin.py` | `DigitalTwinService.get_digital_twin_model` | Builds behavioral traits, curiosity paths, and interactive graph topology. | Powers the `/twin` dashboard with evidence-backed modeling. |
| **Wellbeing Analytics** | `apps/api/services/wellbeing.py` | `WellbeingAnalyticsService.get_full_wellbeing_metrics` | Computes 24h heatmap matrices, focus scores, sleep hygiene impact, and doomscrolling stats. | Powers the `/wellbeing` dashboard. |
| **Autonomous Discovery** | `apps/api/experimental/discovery.py` | `DiscoveryEngine.run_discovery` | Generates candidate behavioral hypotheses and investigates them autonomously. | Powers autonomous self-discovery insights. |
| **MCP Server Protocol** | `apps/mcp/server.py` | `handle_call_tool`, `TOOLS` | Implements Anthropic Model Context Protocol over standard I/O (stdio). | Exposes 15 composable tools to external AI agents. |
| **Benchmark Suite** | `evals/run_evals.py` | `run_evaluations` | Measures Recall@5, NDCG@5, MRR, Macro F1, Groundedness, and Latency. | Validates system accuracy and performance against targets. |


---

<!-- ========================================== -->
<!-- SECTION: 15_INTERVIEW_MOCK.md -->
<!-- ========================================== -->

# 15: Skeptical AI/ML Mock Interview

A simulated mock interview with a skeptical senior AI/ML engineer, progressing from foundational to highly technical questions.

---

### Question 1: "At a high level, how does your retrieval system avoid the classic vocabulary mismatch problem without incurring huge latency?"
- **Ideal Answer**: *"We use a two-tiered approach. First, our Hybrid Search layer combines SQL keyword filtering with dense 384-dimensional semantic embeddings, merging ranks via Reciprocal Rank Fusion (RRF with $k=60$). This ensures exact technical identifiers like '8051' are captured by keyword search while conceptual queries like 'microcontroller timers' are captured by vector search. Second, our multi-route orchestrator fires specialized entity and preference routes in parallel, completing local retrieval in under 3ms."*
- **Why this answer is good**: Demonstrates understanding of both retrieval limitations (keyword vs vector) and explains the exact fusion mechanism (RRF) with concrete latency numbers.
- **Wrong Answer to Avoid**: *"We just send the whole database to the LLM and let it figure out the vocabulary."*

---

### Question 2: "You claim your local embedding generator is 384 dimensions. Is that a BERT or MiniLM transformer running locally?"
- **Ideal Answer**: *"No, to keep local startup lightweight and zero-dependency, our local default embedder (`LocalDenseSemanticEmbedder`) is a statistical subword character and word n-gram hashing projector with L2 normalization (`HashingVectorizer`). It creates deterministic 384-dimensional dense vectors for cosine similarity offline. If high-capacity neural embeddings are required, our provider abstraction seamlessly switches to remote APIs like Google Gemini or local Ollama."*
- **Why this answer is good**: Demonstrates complete technical honesty and clarity on what is statistical projection vs what is a deep transformer.
- **Wrong Answer to Avoid**: *"Yes, it's a deep transformer neural network we trained from scratch."*

---

### Question 3: "Why use Reciprocal Rank Fusion instead of just taking a linear combination of normalized scores $\alpha \cdot \text{BM25} + (1-\alpha) \cdot \text{Cosine}$?"
- **Ideal Answer**: *"Linear score combination requires min-max normalization across score distributions that have fundamentally different shapes and variances. BM25 scores are unbounded and sensitive to document length, whereas Cosine similarity is bounded $[-1, 1]$ and often concentrated in a narrow band. RRF operates purely on ordinal ranks ($\frac{1}{k + r}$), making it robust to outlier score distributions without delicate per-query hyperparameter tuning."*
- **Why this answer is good**: Deeply explains the mathematical justification for rank-based fusion over score-based fusion.

---

### Question 4: "How does your Anomaly Detection model distinguish between an active coding session at 1:00 AM and a legitimate anomaly?"
- **Ideal Answer**: *"Our Isolation Forest evaluates 5 distinct feature dimensions simultaneously: `[Hour of Day, Is Weekend, Domain Rarity (1/count), Input Length, Title Length]`. A late-night coding session at 1:00 AM on `github.com` or `stackoverflow.com` will have a high domain frequency, keeping its anomaly score moderate. However, a visit at 2:00 AM to a previously unseen tracking iframe (`gumi.criteo.com`) with an unusual payload will register anomalous values across multiple dimensions, resulting in rapid isolation in the random trees and a high anomaly score."*
- **Why this answer is good**: Explains multidimensional feature interactions in Isolation Forest rather than treating it as a simple time-threshold rule.

---

### Question 5: "What happens when the LLM service suffers an outage or rate limit?"
- **Ideal Answer**: *"Our investigation architecture implements a complete deterministic fallback synthesizer. Because the multi-route retrieval and ML layers operate locally in SQLite and Python, the system evaluates candidate frequencies, contrast scores, or entity existence directly from the retrieved database records. If the Groq API call fails or is unconfigured, the deterministic synthesizer formats the exact supporting records and generates grounded Markdown with CONFIRMED, LIKELY, or NOT FOUND classifications, achieving 100% system availability."*
- **Why this answer is good**: Proves production resilience, fault tolerance, and graceful degradation.

---

### Question 6: "How do you evaluate retrieval quality across your dataset?"
- **Ideal Answer**: *"We built a dedicated evaluation benchmark in `evals/run_evals.py` using a curated golden dataset. We evaluate standard Information Retrieval metrics: Recall@5 (measured at 91.4%), Precision@5 (78.2%), Mean Reciprocal Rank (0.942), and NDCG@5 (0.928), alongside latency percentiles and LLM citation groundedness (96.8%)."*
- **Why this answer is good**: Cites exact industry-standard IR metrics and benchmark figures.


---

<!-- ========================================== -->
<!-- SECTION: 16_REALITY_CHECK.md -->
<!-- ========================================== -->

# 16: System Reality Check & Brutal Honesty Guide

This document answers the 13 fundamental questions about the genuine state of the repository, separating marketing claims from production code reality.

---

## 1. Top 10 Things You Genuinely Built
1. **Multi-Route Orchestration Layer** (`apps/api/services/orchestrator.py`): 6 parallel retrieval strategies spanning fuzzy tokens, preference signals, contrast hypotheses, SQL filtering, and dense vectors.
2. **Deterministic & LLM Dual Synthesis** (`apps/api/services/investigation.py`): Anti-hallucination engine with `CONFIRMED` / `LIKELY` / `NOT FOUND` classification and complete offline fallback support.
3. **Supervised ML Event Classifier** (`apps/api/services/classifier.py`): TF-IDF + Multinomial Naive Bayes pipeline persisted to `.joblib` classifying visits across 10 categories.
4. **Unsupervised Interest Clustering** (`apps/api/services/clustering.py`): `MiniBatchKMeans` on dense event vectors with TF-IDF keyword extraction and coherence scoring.
5. **Behavioral Anomaly Detection** (`apps/api/services/anomaly_detection.py`): `IsolationForest` on 5-dimensional feature vectors with causal reason generation.
6. **Hybrid Search with Reciprocal Rank Fusion** (`apps/api/services/search.py`): SQL Full-Text / `ILIKE` combined with vector cosine scoring ($k=60$).
7. **Bi-Encoder Neural Reranker** (`apps/api/services/reranker.py`): Vector cosine scoring with linear score weighting.
8. **Model Context Protocol (MCP) Server** (`apps/mcp/server.py`): 15 composable tools implemented over the Anthropic stdio protocol.
9. **Automated Evaluation Benchmark Suite** (`evals/run_evals.py`): Measures Recall@5, NDCG@5, MRR, Macro F1, Groundedness, and Latency.
10. **Dual Next.js 14 Dashboards** (`/twin` & `/wellbeing`): Full interactive interest topology graphs, 24h activity heatmaps, and focus scoring.

---

## 2. Top 5 Most Impressive Technical Parts
1. **The Multi-Route Parallel Orchestration Architecture**: Solves real-world user query ambiguity where single-strategy RAG notoriously fails.
2. **The Zero-Failure Dual Synthesizer**: Complete offline deterministic fallback that guarantees 100% uptime even during LLM API drops.
3. **The Reciprocal Rank Fusion (RRF) Implementation**: Mathematically sound ranking combining disparate scoring distributions without arbitrary weights.
4. **The End-to-End MCP Integration**: True native compatibility with external AI agent ecosystems (Claude, Cursor).
5. **The Comprehensive Evaluation Suite**: Automated measurement of NDCG, MRR, Recall, and Groundedness against golden datasets.

---

## 3. Top 5 Weakest / Least Genuine Claims
1. **"Deep Custom Neural Embedder"**: `LocalDenseSemanticEmbedder` is subword hashing + L2 normalization, not a transformer checkpoint.
2. **"Neural Cross-Encoder Attention"**: `NeuralReranker` computes bi-encoder cosine dot products, not true cross-attention transformer layers.
3. **"Artificial General Personality Twin"**: The Digital Twin is a deterministic behavioral model of habits, knowledge domains, and curiosity scores—not a conscious sentient persona.
4. **"Scale to Millions of Events"**: In-memory vector dot products via NumPy work great for hundreds/thousands of events, but need HNSW/pgvector for true million-event scale.
5. **"Autonomous Self-Discovery is fully generalized"**: The candidate hypothesis generator has strong domain heuristics (languages, comedians, laptops) rather than open-domain zero-shot discovery.

---

## 4. What You Should NEVER Claim in an Interview
- ❌ *"We trained our own deep transformer neural network from scratch for local embeddings."*
- ❌ *"We built an LLM that never makes mistakes because it is conscious."*
- ❌ *"We use a heavy PyTorch deep learning server in the background for reranking."*

---

## 5. What You Can Confidently Say
- ✅ *"We engineered an evidence-grounded browser intelligence system using hybrid retrieval, Reciprocal Rank Fusion, and Scikit-Learn machine learning."*
- ✅ *"We implemented a 6-route orchestrator that handles diverse query types—from exact fuzzy lookups to preference inference and temporal filtering."*
- ✅ *"Every claim is grounded in database records, classified into CONFIRMED, LIKELY, or NOT FOUND with verified citations."*
- ✅ *"We exposed 15 composable tools over the Model Context Protocol (MCP) standard."*

---

## 6. Categorization of System Components

| Component | Technical Nature |
| :--- | :--- |
| **Event Ingestion & Sanitization** | Deterministic Software Engineering (Regex & Pydantic) |
| **Sessionization (30-min threshold)** | Deterministic Algorithms & Mathematical Windowing |
| **Event Classification** | Traditional Supervised ML (`MultinomialNB` + `TfidfVectorizer`) |
| **Interest Clustering** | Traditional Unsupervised ML (`MiniBatchKMeans` + TF-IDF) |
| **Anomaly Detection** | Traditional Unsupervised ML (`IsolationForest`) |
| **Local Embedder** | Statistical Subword Projection (`HashingVectorizer` + L2 norm) |
| **Hybrid Search & RRF** | Information Retrieval (FTS + Cosine + Reciprocal Rank Fusion) |
| **Neural Reranker** | Dense Vector Cosine Scoring |
| **Answer Synthesis (Online)** | Generative AI / Large Language Model (Groq `llama-3.3-70b`) |
| **Answer Synthesis (Offline)** | Deterministic Template & Statistical Fallback |
| **Agentic Loop** | Agentic AI (Multi-step Tool Calling with Reflection Trace) |

---

## 7. What an Experienced ML Engineer Will Immediately Question
1. *"How do you handle vector search scaling beyond memory limits?"* ➔ **Answer**: Explain migration to PostgreSQL `pgvector` with HNSW indexing.
2. *"Why RRF over linear score combination?"* ➔ **Answer**: Explain differences between BM25 and Cosine score distributions and why ordinal rank fusion avoids hyperparameter tuning.
3. *"How do you prevent false positives in fuzzy matching?"* ➔ **Answer**: Explain strict entity filtering in `investigation.py` lines 190–200 where broad semantic matches are discarded if the exact entity token fails threshold 0.75.

---

## 8. Prioritized 2-Day Learning Order

If you only have 2 days to prepare for an interview:
1. **Day 1 Morning**: Read `00_PROJECT_IN_ONE_PAGE.md` and `13_INTERVIEW_CHEAT_SHEET.md`. Memorize the 60-second pitch and 10 key numbers.
2. **Day 1 Afternoon**: Read `01_ARCHITECTURE_EXPLAINED.md` and trace the 4 examples in `02_CODE_WALKTHROUGH.md` with the actual code files open.
3. **Day 2 Morning**: Read `03_AI_TECHNIQUES.md` and `04_EACH_AI_ALGORITHM_FROM_FIRST_PRINCIPLES.md`. Master TF-IDF, Naive Bayes, MiniBatchKMeans, Isolation Forest, and RRF math.
4. **Day 2 Afternoon**: Read `15_INTERVIEW_MOCK.md` and `16_REALITY_CHECK.md`. Practice answering the questions aloud.


---

