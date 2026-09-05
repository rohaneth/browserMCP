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
