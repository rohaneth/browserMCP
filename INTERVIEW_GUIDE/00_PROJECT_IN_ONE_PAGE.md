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
        │  (Captures click
        s, inputs, urls, titles, page text)
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
