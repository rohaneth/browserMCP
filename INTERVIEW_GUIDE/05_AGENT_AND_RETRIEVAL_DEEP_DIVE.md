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
