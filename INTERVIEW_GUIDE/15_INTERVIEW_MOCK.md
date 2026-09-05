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
