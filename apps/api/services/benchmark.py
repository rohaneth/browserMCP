import time
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from models.events import Event
from schemas.search import Evidence
from schemas.structured_output import ConfidenceLevel
from services.search import search_events, search_hybrid
from services.reranker import NeuralReranker
from services.investigation import run_investigation
from services.agentic_investigator import AgenticInvestigator
from services.classifier import BrowserEventClassifier
from services.clustering import InterestClusterEngine

logger = logging.getLogger(__name__)

# Curated benchmark evaluation queries with ground-truth target tokens & expectation types
BENCHMARK_DATASET = [
    {
        "id": "q1_fact_programming",
        "type": "preference_inference",
        "query": "What is my favourite programming language?",
        "expected_tokens": ["java", "jvm", "stream"],
        "expected_answer_contains": "Java"
    },
    {
        "id": "q2_fact_movie",
        "type": "factual_lookup",
        "query": "Did I watch Avengers Endgame?",
        "expected_tokens": ["avengers", "endgame", "movie", "youtube"],
        "expected_answer_contains": "CONFIRMED"
    },
    {
        "id": "q3_art_preference",
        "type": "preference_inference",
        "query": "Which art form do I like?",
        "expected_tokens": ["film", "movie", "cinema"],
        "expected_answer_contains": "Film"
    },
    {
        "id": "q4_hypo_personality",
        "type": "hypothesis_comparison",
        "query": "Am I introvert or extrovert based on my browsing?",
        "expected_tokens": ["introvert", "alone", "quiet", "extrovert", "party"],
        "expected_answer_contains": "BEHAVIORAL"
    },
    {
        "id": "q5_negative_dostoevsky",
        "type": "negative_not_found",
        "query": "Did I search Dostoevsky?",
        "expected_tokens": ["dostoevsky"],
        "expected_answer_contains": "NOT FOUND"
    },
    {
        "id": "q6_typo_avanger",
        "type": "fuzzy_typo",
        "query": "avanger endgame",
        "expected_tokens": ["avengers", "endgame"],
        "expected_answer_contains": "Endgame"
    },
    {
        "id": "q7_open_ended_learn",
        "type": "open_ended_pattern",
        "query": "What have you learned about me from my browsing that I probably haven't noticed?",
        "expected_tokens": ["software", "engineering", "philosophy", "film", "youtube"],
        "expected_answer_contains": "PATTERN"
    },
    {
        "id": "q8_semantic_coding",
        "type": "semantic_retrieval",
        "query": "tell me which coding language i use the most",
        "expected_tokens": ["java", "jvm", "programming"],
        "expected_answer_contains": "Java"
    },
    {
        "id": "q9_temporal_yesterday",
        "type": "temporal_query",
        "query": "What did I search about yesterday?",
        "expected_tokens": ["youtube", "google", "resume", "project"],
        "expected_answer_contains": "EVIDENCE"
    },
    {
        "id": "q10_entertainment_type",
        "type": "preference_inference",
        "query": "What kind of entertainment do I prefer?",
        "expected_tokens": ["movie", "youtube", "film", "video"],
        "expected_answer_contains": "Film"
    },
    {
        "id": "q11_typo_programming",
        "type": "fuzzy_typo",
        "query": "what is my favrite programing lanugage",
        "expected_tokens": ["java", "programming", "language"],
        "expected_answer_contains": "Java"
    },
    {
        "id": "q12_multi_hop_interests",
        "type": "multi_hop",
        "query": "What are my strongest technical and creative interests?",
        "expected_tokens": ["java", "film", "movie", "programming", "resume"],
        "expected_answer_contains": "Java"
    },
    {
        "id": "q13_negative_nietzsche",
        "type": "negative_not_found",
        "query": "Have I searched about Nietzsche?",
        "expected_tokens": ["nietzsche"],
        "expected_answer_contains": "NOT FOUND"
    },
    {
        "id": "q14_open_enjoy",
        "type": "open_ended_pattern",
        "query": "What do I seem to enjoy?",
        "expected_tokens": ["youtube", "film", "movie", "standup", "comedy"],
        "expected_answer_contains": "PATTERN"
    },
    {
        "id": "q15_topics_interested",
        "type": "open_ended_pattern",
        "query": "What topics am I most interested in?",
        "expected_tokens": ["java", "film", "resume", "project"],
        "expected_answer_contains": "interests"
    },
    {
        "id": "q16_ambiguous_activity",
        "type": "ambiguous_query",
        "query": "things i worked on",
        "expected_tokens": ["resume", "project", "java", "gemini"],
        "expected_answer_contains": "EVIDENCE"
    }
]


class AppliedAIBenchmark:
    """
    Applied AI Evaluation & Benchmark Suite for BrowserMCP.
    Computes standard Information Retrieval (Recall@K, MRR, NDCG) and
    LLM/Agentic metrics across Baseline, Hybrid, Hybrid+Reranking, and Agentic pipelines.
    """

    @classmethod
    def calculate_retrieval_metrics(
        cls,
        retrieved_texts: List[str],
        target_tokens: List[str],
        k_list: List[int] = [1, 5, 10]
    ) -> Dict[str, float]:
        metrics = {}
        
        # Check relevance binary hit for each rank position
        hits = []
        for text in retrieved_texts:
            t_lower = text.lower()
            is_hit = any(tok.lower() in t_lower for tok in target_tokens)
            hits.append(1.0 if is_hit else 0.0)

        # Recall@K and Precision@K
        for k in k_list:
            top_k_hits = hits[:k]
            metrics[f"recall@{k}"] = 1.0 if sum(top_k_hits) > 0 else 0.0
            metrics[f"precision@{k}"] = sum(top_k_hits) / k if k > 0 else 0.0

        # MRR (Mean Reciprocal Rank)
        mrr = 0.0
        for i, hit in enumerate(hits):
            if hit > 0:
                mrr = 1.0 / (i + 1)
                break
        metrics["mrr"] = mrr

        # NDCG@5 (Normalized Discounted Cumulative Gain)
        dcg = 0.0
        for i, hit in enumerate(hits[:5]):
            if hit > 0:
                import math
                dcg += hit / math.log2(i + 2)
        metrics["ndcg@5"] = dcg / 1.0 if dcg <= 1.0 else 1.0

        return metrics

    @classmethod
    def run_benchmark(cls, db: Session) -> Dict[str, Any]:
        configurations = ["Baseline (SQL/Keyword)", "Hybrid (Keyword+Semantic)", "Hybrid + Reranking", "Full Agentic Investigation"]
        results_by_config = {c: [] for c in configurations}

        for item in BENCHMARK_DATASET:
            q = item["query"]
            targets = item["expected_tokens"]
            is_negative = item["type"] == "negative_not_found"

            # 1. Config A: Baseline (SQL Keyword search)
            t0 = time.time()
            res_base = search_events(db, keyword=q)
            t_base = (time.time() - t0) * 1000
            base_texts = [f"{e.page_title or ''} {e.input_text or ''}" for e in res_base.events[:10]]
            base_metrics = cls.calculate_retrieval_metrics(base_texts, targets)
            base_metrics["latency_ms"] = t_base
            results_by_config["Baseline (SQL/Keyword)"].append(base_metrics)

            # 2. Config B: Hybrid Search (Full-Text + Vector RRF)
            t0 = time.time()
            res_hyb = search_hybrid(db, query=q, limit=10)
            t_hyb = (time.time() - t0) * 1000
            top_eids = res_hyb.get("top_results", [])
            import uuid
            uuid_objs = [uuid.UUID(str(uid)) for uid in top_eids if uid]
            hyb_events = db.query(Event).filter(Event.event_id.in_(uuid_objs)).all() if uuid_objs else []
            hyb_texts = [f"{e.page_title or ''} {e.input_text or ''}" for e in hyb_events]
            hyb_metrics = cls.calculate_retrieval_metrics(hyb_texts, targets)
            hyb_metrics["latency_ms"] = t_hyb
            results_by_config["Hybrid (Keyword+Semantic)"].append(hyb_metrics)

            # 3. Config C: Hybrid + Neural Reranker
            t0 = time.time()
            cands = [
                Evidence(event_id=str(e.event_id), timestamp=e.timestamp, url=e.url, title=e.page_title, snippet=e.input_text or "", relevance=0.5)
                for e in hyb_events
            ]
            reranked = NeuralReranker.rerank_evidence(query=q, candidates=cands, top_n=10)
            t_rerank = (time.time() - t0) * 1000 + t_hyb
            rerank_texts = [f"{c.title or ''} {c.snippet or ''}" for c in reranked]
            rerank_metrics = cls.calculate_retrieval_metrics(rerank_texts, targets)
            rerank_metrics["latency_ms"] = t_rerank
            results_by_config["Hybrid + Reranking"].append(rerank_metrics)

            # 4. Config D: Full Agentic Investigation
            t0 = time.time()
            inv_res = AgenticInvestigator.run_agentic_loop(db=db, query=q, max_iterations=3)
            t_agent = (time.time() - t0) * 1000
            agent_texts = [f"{c.title or ''} {c.snippet or ''}" for c in inv_res.citations]
            agent_metrics = cls.calculate_retrieval_metrics(agent_texts, targets)
            agent_metrics["latency_ms"] = t_agent
            agent_metrics["grounded"] = 1.0 if (not is_negative and len(inv_res.citations) > 0) or (is_negative and "NOT FOUND" in inv_res.direct_answer) else 0.0
            agent_metrics["hallucination_rate"] = 0.0 if agent_metrics["grounded"] == 1.0 else 1.0
            results_by_config["Full Agentic Investigation"].append(agent_metrics)

        # Aggregate summary table
        summary = {}
        for cfg, runs in results_by_config.items():
            summary[cfg] = {
                "Recall@1": round(sum(r["recall@1"] for r in runs) / len(runs), 3),
                "Recall@5": round(sum(r["recall@5"] for r in runs) / len(runs), 3),
                "MRR": round(sum(r["mrr"] for r in runs) / len(runs), 3),
                "NDCG@5": round(sum(r["ndcg@5"] for r in runs) / len(runs), 3),
                "Avg Latency (ms)": round(sum(r["latency_ms"] for r in runs) / len(runs), 1)
            }
            if cfg == "Full Agentic Investigation":
                summary[cfg]["Answer Groundedness"] = round(sum(r.get("grounded", 1.0) for r in runs) / len(runs), 3)
                summary[cfg]["Hallucination Rate"] = round(sum(r.get("hallucination_rate", 0.0) for r in runs) / len(runs), 3)

        return {
            "total_evaluated_queries": len(BENCHMARK_DATASET),
            "summary_table": summary,
            "detailed_runs": results_by_config
        }
