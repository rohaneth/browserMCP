# 14: Code-to-Concept Map

A comprehensive mapping of every conceptual component in the system to its exact source file, classes, functions, and architectural rationale.

---

| Concept | Actual File Path | Class / Function | What It Does | Why It Matters |
| :--- | :--- | :--- | :--- | :--- |
| **Multi-Route Orchestration** | `apps/api/services/orchestrator.py` | `GeneralizedInvestigationOrchestrator.execute_multi_route_retrieval` | Runs 6 parallel retrieval strategies across fuzzy tokens, heuristics, SQL, vectors, and memory. | Prevents retrieval bottlenecking on a single search method. |
| **Grounded Investigation** | `apps/api/services/investigation.py` | `run_investigation` | Manages query workflow, calls orchestrator, applies reranking, and synthesizes grounded answers. | Core entry point guaranteeing zero hallucination. |
| **Agentic Investigation** | `apps/api/services/agentic_investigator.py` | `AgenticInvestigator.run_agentic_loop` | Executes multi-step tool calling loop with step budgets, reflection, and execution traces. | Solves complex, multi-hop user inquiries. |
| **Supervised Classifier** | `apps/api/services/classifier.py` | `BrowserEventClassifier` | Runs `TfidfVectorizer` + `MultinomialNB` pipeline to classify events into 10 categories. | Fast local categorization without LLM API costs. |
| **Unsupervised Clustering** | `apps/api/services/clustering.py` | `InterestClusterEngine.discover_clusters` | Runs `MiniBatchKMeans` and TF-IDF keyword extraction on 384-d event vectors. | Discovers latent interest topics and computes semantic coherence. |
| **Anomaly Detection** | `apps/api/services/anomaly_detection.py` | `BehavioralAnomalyDetector.detect_anomalies` | Runs `IsolationForest` on 5-d behavioral features (`[hour, is_weekend, rarity, in_len, title_len]`). | Flags unusual late-night activity, rare domains, and anomalous payloads. |
| **Content Recommendations** | `apps/api/services/recommendation.py` | `RecommendationEngine.get_recommendations` | Computes cosine similarity between cluster centroids and curated topic candidates. | Recommends relevant learning paths with non-hallucinated rationales. |
| **Dense Embeddings** | `apps/api/services/embeddings.py` | `LocalDenseSemanticEmbedder`, `RemoteAPIEmbedder` | Generates 384-d dense vectors via subword/word n-gram hashing or remote APIs. | Powers semantic vector search across all events and memories. |
| **Hybrid Search & RRF** | `apps/api/services/search.py` | `search_hybrid` | Blends SQL keyword `ILIKE` and vector dot-products using Reciprocal Rank Fusion ($k=60$). | Solves vocabulary mismatch while preserving exact keyword precision. |
| **Neural Reranking** | `apps/api/services/reranker.py` | `NeuralReranker.rerank_evidence` | Scores candidate records using $(0.85 \times \text{semantic}) + (0.15 \times \text{initial})$. | Prioritizes high-relevance evidence at top ranks. |
| **Preference Inference** | `apps/api/services/preference.py` | `infer_programming_preference`, `infer_philosophy_preference`, etc. | Scans entire database for weighted token frequencies and search inputs. | Quantifies user affinities and detects favourite languages/topics. |
| **Contrast Hypotheses** | `apps/api/services/general_inference.py` | `GeneralInferenceEngine.evaluate_contrast_hypotheses` | Compares relative evidence volume between two competing hypotheses (e.g. A vs B). | Answers comparative user questions accurately. |
| **Fuzzy Matching** | `apps/api/utils/fuzzy.py` | `find_entity_matches_in_text` | Computes Levenshtein similarity ratio ($\ge 0.75$) using `difflib.SequenceMatcher`. | Resolves typos and spelling variants in user queries. |
| **PII Sanitization** | `apps/api/utils/privacy.py` | `sanitize_text`, `sanitize_event` | Redacts API keys, auth tokens, passwords, and sensitive regex patterns. | Ensures private secrets are never persisted or sent to LLMs. |
| **Sessionization** | `apps/api/utils/sessionization.py` | `sessionize_events` | Groups events into contiguous blocks based on 30-minute inactivity threshold. | Computes session durations, focus scores, and deep work blocks. |
| **Digital Twin Service** | `apps/api/services/twin.py` | `DigitalTwinService.get_digital_twin_model` | Builds behavioral traits, curiosity paths, and interactive graph topology. | Powers the `/twin` dashboard with evidence-backed modeling. |
| **Wellbeing Analytics** | `apps/api/services/wellbeing.py` | `WellbeingAnalyticsService.get_full_wellbeing_metrics` | Computes 24h heatmap matrices, focus scores, sleep hygiene impact, and doomscrolling stats. | Powers the `/wellbeing` dashboard. |
| **Autonomous Discovery** | `apps/api/experimental/discovery.py` | `DiscoveryEngine.run_discovery` | Generates candidate behavioral hypotheses and investigates them autonomously. | Powers autonomous self-discovery insights. |
| **MCP Server Protocol** | `apps/mcp/server.py` | `handle_call_tool`, `TOOLS` | Implements Anthropic Model Context Protocol over standard I/O (stdio). | Exposes 15 composable tools to external AI agents. |
| **Benchmark Suite** | `evals/run_evals.py` | `run_evaluations` | Measures Recall@5, NDCG@5, MRR, Macro F1, Groundedness, and Latency. | Validates system accuracy and performance against targets. |
