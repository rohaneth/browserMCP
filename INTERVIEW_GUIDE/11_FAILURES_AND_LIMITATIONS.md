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
