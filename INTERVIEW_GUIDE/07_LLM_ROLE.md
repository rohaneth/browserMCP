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
