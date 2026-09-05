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
