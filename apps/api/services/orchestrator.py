import logging
import re
from typing import Dict, Any, List, Tuple, Optional, Set
from collections import Counter
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from models.events import Event
from schemas.search import Evidence
from utils.normalization import extract_url_search_params
from utils.fuzzy import normalize_string, extract_fuzzy_keywords, find_entity_matches_in_text
from services.search import search_hybrid
from services.preference import (
    detect_preference_category,
    infer_programming_preference,
    infer_comedian_preference,
    infer_entertainment_preference,
    infer_art_form_preference,
    infer_authors_literature_preference,
    infer_philosophy_preference
)
from services.general_inference import GeneralInferenceEngine

logger = logging.getLogger(__name__)


class GeneralizedInvestigationOrchestrator:
    """
    Generalized multi-route evidence retrieval, aggregation, and hypothesis engine.
    Discovers relevant signals across the entire database without bottlenecking
    on a single predefined intent classification.
    """

    @classmethod
    def rewrite_and_expand_query(cls, query: str) -> Dict[str, Any]:
        """
        Extracts semantic interpretations, entity candidates, contrast hypotheses,
        temporal anchors, and broad topic signals from user queries.
        """
        q_norm = normalize_string(query)
        q_lower = query.lower()

        # 1. Check if this is an open-ended behavioral/pattern discovery question
        is_open_ended = any(k in q_norm for k in [
            "learned about me", "learn about me", "haven t noticed", "havent noticed",
            "what do i seem to enjoy", "what do i enjoy", "what topics am i", "topics am i interested in",
            "kind of person", "patterns do you notice", "browsing patterns", "my strongest interests",
            "tell me about myself", "what are my habits"
        ])

        # 2. Check contrast / hypothesis
        contrast_meta = GeneralInferenceEngine.detect_inference_question(query)

        # 3. Check specific category hints
        category_hint = detect_preference_category(query)

        # 4. Check domain target
        target_domain = None
        for d in ["stackoverflow.com", "google.com", "youtube.com", "amazon.in", "github.com", "reddit.com"]:
            if d.split(".")[0] in q_lower:
                target_domain = d
                break

        # 5. Extract core entity/concept tokens
        content_keywords = extract_fuzzy_keywords(query)
        
        # 6. Temporal bounds
        time_start = None
        time_end = None
        now = datetime.utcnow()
        if "yesterday" in q_lower:
            time_start = now - datetime.resolution * 0  # Placeholder, handled dynamically
            # 2 days window
            from datetime import timedelta
            time_start = now - timedelta(days=2)
            time_end = now
        elif "today" in q_lower:
            from datetime import timedelta
            time_start = now - timedelta(days=1)

        return {
            "raw_query": query,
            "normalized_query": q_norm,
            "is_open_ended": is_open_ended,
            "contrast_meta": contrast_meta,
            "category_hint": category_hint,
            "target_domain": target_domain,
            "content_keywords": content_keywords,
            "time_start": time_start,
            "time_end": time_end
        }

    @classmethod
    def execute_multi_route_retrieval(cls, db: Session, query: str) -> Dict[str, Any]:
        """
        Executes parallel retrieval routes across:
        - Route 1: Exact & Fuzzy Entity/Keyword Matching
        - Route 2: Category Preference Signal Aggregation
        - Route 3: General Inference & Hypothesis Comparison
        - Route 4: Structured SQL Filtering (domains, inputs, time)
        - Route 5: Dense Hybrid Semantic Embeddings
        - Route 6: Open-ended Behavioral Pattern Mining
        """
        meta = cls.rewrite_and_expand_query(query)
        all_events = db.query(Event).all()

        candidates_by_route: Dict[str, List[Event]] = {
            "entity_fuzzy": [],
            "category_preference": [],
            "hypothesis_inference": [],
            "structured_sql": [],
            "hybrid_semantic": [],
            "behavioral_mining": []
        }

        # Track score per event for fusion
        event_scores: Dict[str, float] = {}
        event_map: Dict[str, Event] = {}
        evidence_reasons: Dict[str, List[str]] = {}

        # -------------------------------------------------------------
        # Route 1: Exact & Fuzzy Entity / Content Token Resolution
        # -------------------------------------------------------------
        kws = meta["content_keywords"]
        if kws:
            for e in all_events:
                inp = e.input_text or extract_url_search_params(e.url) or ""
                title = e.page_title or ""
                url = e.url or ""
                content = (e.content or "")[:400]
                text_blob = f"{inp} {title} {url} {content}".lower()

                # Test entire query keywords together
                full_cand = " ".join(kws)
                matched_full, score_full = find_entity_matches_in_text(full_cand, text_blob, threshold=0.75)
                if matched_full:
                    eid = str(e.event_id)
                    event_map[eid] = e
                    event_scores[eid] = event_scores.get(eid, 0.0) + (score_full * 5.0)
                    candidates_by_route["entity_fuzzy"].append(e)
                    if eid not in evidence_reasons: evidence_reasons[eid] = []
                    evidence_reasons[eid].append(f"Fuzzy Entity Match: '{full_cand}' (score: {round(score_full, 2)})")
                else:
                    # Test individual keywords
                    for kw in kws:
                        if len(kw) >= 3:
                            matched, score = find_entity_matches_in_text(kw, text_blob, threshold=0.8)
                            if matched:
                                eid = str(e.event_id)
                                event_map[eid] = e
                                event_scores[eid] = event_scores.get(eid, 0.0) + (score * 2.0)
                                candidates_by_route["entity_fuzzy"].append(e)
                                if eid not in evidence_reasons: evidence_reasons[eid] = []
                                evidence_reasons[eid].append(f"Keyword Match: '{kw}'")
                                break

        # -------------------------------------------------------------
        # Route 2: Category Preference Evaluation
        # -------------------------------------------------------------
        cat_hint = meta["category_hint"]
        pref_data = None
        if cat_hint:
            if cat_hint == "programming_language":
                pref_data, pref_evs = infer_programming_preference(db)
            elif cat_hint == "art_form":
                pref_data, pref_evs = infer_art_form_preference(db)
            elif cat_hint == "authors_literature":
                pref_data, pref_evs = infer_authors_literature_preference(db)
            elif cat_hint == "philosophy":
                pref_data, pref_evs = infer_philosophy_preference(db)
            elif cat_hint == "comedian":
                pref_data, pref_evs = infer_comedian_preference(db)
            else:
                pref_data, pref_evs = infer_entertainment_preference(db)

            for e in pref_evs:
                eid = str(e.event_id)
                event_map[eid] = e
                event_scores[eid] = event_scores.get(eid, 0.0) + 4.0
                candidates_by_route["category_preference"].append(e)
                if eid not in evidence_reasons: evidence_reasons[eid] = []
                evidence_reasons[eid].append(f"Preference Signal for {cat_hint}")

        # -------------------------------------------------------------
        # Route 3: General Inference & Hypothesis Comparison
        # -------------------------------------------------------------
        inf_result = None
        if meta["contrast_meta"]:
            h_a = meta["contrast_meta"]["hypothesis_a"]
            h_b = meta["contrast_meta"]["hypothesis_b"]
            inf_result, inf_evs = GeneralInferenceEngine.evaluate_contrast_hypotheses(db, query, h_a, h_b)
            for e in inf_evs:
                eid = str(e.event_id)
                event_map[eid] = e
                event_scores[eid] = event_scores.get(eid, 0.0) + 3.5
                candidates_by_route["hypothesis_inference"].append(e)
                if eid not in evidence_reasons: evidence_reasons[eid] = []
                evidence_reasons[eid].append(f"Hypothesis comparative signal ({h_a} vs {h_b})")

        # -------------------------------------------------------------
        # Route 4: Structured SQL Filtering (Domain / Input / Time)
        # -------------------------------------------------------------
        if meta["target_domain"] or meta["time_start"]:
            db_q = db.query(Event)
            if meta["target_domain"]:
                db_q = db_q.filter(Event.domain.ilike(f"%{meta['target_domain']}%"))
            if meta["time_start"]:
                db_q = db_q.filter(Event.timestamp >= meta["time_start"])
            sql_evs = db_q.order_by(Event.timestamp.desc()).limit(50).all()
            for e in sql_evs:
                eid = str(e.event_id)
                event_map[eid] = e
                event_scores[eid] = event_scores.get(eid, 0.0) + 3.0
                candidates_by_route["structured_sql"].append(e)
                if eid not in evidence_reasons: evidence_reasons[eid] = []
                evidence_reasons[eid].append("Domain/Temporal Structured Filter")

        # -------------------------------------------------------------
        # Route 5: Dense Hybrid Semantic Embeddings
        # -------------------------------------------------------------
        try:
            search_res = search_hybrid(db, query, limit=25)
            top_uids = search_res.get("top_results", [])
            if top_uids:
                hyb_evs = db.query(Event).filter(Event.event_id.in_(top_uids)).all()
                for e in hyb_evs:
                    eid = str(e.event_id)
                    event_map[eid] = e
                    event_scores[eid] = event_scores.get(eid, 0.0) + 2.5
                    candidates_by_route["hybrid_semantic"].append(e)
                    if eid not in evidence_reasons: evidence_reasons[eid] = []
                    evidence_reasons[eid].append("Hybrid Semantic Embedding Match")
        except Exception as e:
            logger.warning(f"Hybrid search fallback in orchestrator: {e}")

        # -------------------------------------------------------------
        # Route 6: Open-ended Behavioral Pattern Mining
        # -------------------------------------------------------------
        if meta["is_open_ended"] or len(event_map) == 0:
            # Aggregate search submissions and high-engagement domains
            search_events = [
                e for e in all_events
                if (e.input_text or extract_url_search_params(e.url))
            ]
            for e in search_events[-30:]:
                eid = str(e.event_id)
                event_map[eid] = e
                event_scores[eid] = event_scores.get(eid, 0.0) + 2.0
                candidates_by_route["behavioral_mining"].append(e)
                if eid not in evidence_reasons: evidence_reasons[eid] = []
                evidence_reasons[eid].append("Active Search Input Pattern")

        # -------------------------------------------------------------
        # Evidence Fusion & Deduplication
        # -------------------------------------------------------------
        sorted_eids = sorted(event_scores.keys(), key=lambda eid: event_scores[eid], reverse=True)
        fused_events = [event_map[eid] for eid in sorted_eids]

        evidence_list: List[Evidence] = []
        for e in fused_events:
            eid = str(e.event_id)
            inp = e.input_text or extract_url_search_params(e.url) or ""
            snippet = f"[{e.event_type}] Domain: {e.domain} | Title: {e.page_title or 'N/A'}"
            if inp:
                snippet += f" | Input/Search: '{inp}'"
            if eid in evidence_reasons:
                snippet += f" ({', '.join(evidence_reasons[eid][:2])})"

            evidence_list.append(
                Evidence(
                    event_id=eid,
                    timestamp=e.timestamp,
                    url=e.url,
                    title=e.page_title,
                    snippet=snippet,
                    relevance=round(min(1.0, event_scores.get(eid, 0.5) / 5.0), 2)
                )
            )

        return {
            "meta": meta,
            "route_counts": {k: len(v) for k, v in candidates_by_route.items()},
            "fused_events": fused_events,
            "evidence_list": evidence_list,
            "pref_data": pref_data,
            "inf_result": inf_result,
            "total_candidates": len(fused_events)
        }
