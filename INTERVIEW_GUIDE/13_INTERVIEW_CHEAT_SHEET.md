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
