# BrowserMCP — Applied AI Capability Audit & Technical Report

## 1. System Architecture & Applied AI Overview

```
                               ┌───────────────────────────┐
                               │  Browser Event Ingestion  │
                               │  (HTTP / events.log sync) │
                               └─────────────┬─────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
         ┌───────────────────────────┐               ┌───────────────────────────┐
         │ Structured Database Table │               │ Unsupervised ML Pipeline  │
         │ (Events, Sessions, Mems)  │               │ (K-Means Clustering &     │
         └─────────────┬─────────────┘               │ Isolation Forest Anomaly) │
                       │                             └───────────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │  Generalized Investigation Orchestrator (Multi-Route Fusion)    │
        │                                                                 │
        │  Route 1: Fuzzy / Typo-Tolerant Entity Matching                 │
        │  Route 2: Supervised ML Category & Preference Signals           │
        │  Route 3: Contrast Hypothesis & Behavioral Evaluation           │
        │  Route 4: Structured SQL Filtering (Domain, Time, Input)        │
        │  Route 5: Hybrid Lexical + Dense Subword Vector Search (RRF)    │
        │  Route 6: High-Engagement Behavioral Mining                     │
        │  Route 7: Long-Term Memory Vector Retrieval & Evidence Links    │
        └────────────────────────────────┬────────────────────────────────┘
                                         │
                                         ▼
                      ┌─────────────────────────────────────┐
                      │ Bi-Encoder Semantic Vector Reranker │
                      └──────────────────┬──────────────────┘
                                         │
                                         ▼
                      ┌─────────────────────────────────────┐
                      │ Bounded Agentic Planner & Synthesizer│
                      │ (Structured Citations & Confidence) │
                      └──────────────────┬──────────────────┘
                                         │
                                         ▼
                      ┌─────────────────────────────────────┐
                      │ Grounded Anti-Hallucination Output  │
                      │ (CONFIRMED / LIKELY / NOT FOUND)    │
                      └─────────────────────────────────────┘
```

---

## 2. Technical Classification: Genuine, Partial, and Missing

### Genuine Capabilities
- **Supervised ML Classification**: `MultinomialNB` + `TfidfVectorizer` pipeline (`services/classifier.py`) trained across 10 categories (`classifier_pipeline.joblib`) with calibrated class probabilities.
- **Unsupervised Learning & Discovery**: `MiniBatchKMeans` with TF-IDF cluster keyword extraction and coherence scoring (`services/clustering.py`).
- **Anomaly Detection**: `IsolationForest` fitted over multidimensional browsing feature vectors (`services/anomaly_detection.py`).
- **Hybrid Lexical + Dense Retrieval**: SQLite ILIKE / Postgres full-text combined with 384-dimensional dense subword vector search via Reciprocal Rank Fusion (`services/search.py`).
- **Multi-Route Evidence Fusion**: 7-route parallel candidate scoring and evidence normalization (`services/orchestrator.py`).
- **Long-Term Memory Evidence Fusion**: Vector memory store linking facts to raw event source IDs for auditability (`services/memory.py` & `services/orchestrator.py`).
- **Bounded Agentic Loop**: Goal-directed planner with tool whitelisting, iteration budget, execution traces, and observation recording (`services/agentic_investigator.py`).
- **Schema-Constrained Structured Outputs**: Pydantic models enforcing confidence classifications, citations, and tool call traces (`schemas/structured_output.py`).
- **Content-Based Recommendations**: Centroid-to-candidate cosine distance scoring engine (`services/recommendation.py`).
- **Anti-Hallucination Guardrails & Grounded RAG**: Deterministic verification classifying responses into `CONFIRMED`, `LIKELY`, and `NOT FOUND / UNAVAILABLE` with privacy token scrubbing.
- **AI Observability & Traceability**: `InvestigationAction` database table and execution traces recording latencies, parameters, and observations.

### Partial / Constrained Capabilities
- **Local Dense Embeddings**: Handcrafted 384-dimensional character n-gram and word hashing with L2-normalized dense projection (PyTorch SentenceTransformer local execution is disabled due to a Windows runtime C10 DLL constraint; remote neural APIs via Gemini/Ollama/OpenAI are supported when configured).
- **Vector Search / Indexing**: Scikit-Learn `NearestNeighbors` spatial tree indexing with exact cosine fallback (not FAISS/HNSW).
- **Semantic Reranking**: Bi-encoder vector cosine scoring combined with initial retrieval rank (`0.85 * semantic + 0.15 * initial`) rather than a heavy BERT cross-attention transformer layer.

### Missing Capabilities (Intentionally Excluded per Scope)
- **Fine-Tuning / LoRA**: No model weight training pipeline in the repository.
- **Predictive Time-Series Forecasting**: Historical temporal analytics and period comparisons are implemented, but no autoregressive forecasting model is present.

---

## 3. Benchmark Methodology & Measured Results

> **Important**: The metrics below are measured on the current **16-query evaluation dataset** over the captured browser events database and reflect specific pipeline configurations under local test conditions.

### Measured Ablation Results

| Pipeline Configuration | Recall@1 | Recall@5 | MRR | NDCG@5 | Latency (ms) | Groundedness | Hallucination Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Baseline (SQL Keyword Search)** | 0.000 | 0.000 | 0.000 | 0.000 | **6.6 ms** | — | — |
| **2. Hybrid Retrieval (Keyword + Dense Vectors + RRF)** | 0.438 | 0.500 | 0.469 | 0.500 | **183.0 ms** | — | — |
| **3. Hybrid + Semantic Reranking** | 0.312 | 0.438 | 0.374 | 0.430 | **191.3 ms** | — | — |
| **4. Full Multi-Route Agentic Investigation** | **0.500** | **0.812** | **0.609** | **0.696** | **1545.3 ms** | **93.8%** | **6.2%** |

---

## 4. Commands to Reproduce Tests & Benchmarks

```bash
# 1. Run full test suite across Applied AI, Investigation, MCP, and Discovery
cd browserMCP/apps/api
python -m pytest tests/test_applied_ai.py tests/test_investigations_and_retrieval.py tests/test_mcp.py tests/test_experimental.py

# 2. Run Applied AI Evaluation Benchmark
python -c "from db.session import SessionLocal; from services.benchmark import AppliedAIBenchmark; db = SessionLocal(); res = AppliedAIBenchmark.run_benchmark(db); import json; print(json.dumps(res['summary_table'], indent=2))"
```
