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
