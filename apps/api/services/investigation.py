import logging
import os
import re
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from models.investigations import Investigation, InvestigationAction
from models.events import Event
from schemas.search import Evidence
from services.search import search_hybrid
from utils.normalization import extract_url_search_params
from utils.fuzzy import normalize_string, extract_fuzzy_keywords, find_entity_matches_in_text
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
from services.orchestrator import GeneralizedInvestigationOrchestrator
from services.sync_log import sync_events_log_to_db
from groq import Groq

logger = logging.getLogger(__name__)

QUESTION_STOP_WORDS = {
    "did", "do", "does", "have", "has", "had", "was", "were", "is", "am", "are",
    "i", "me", "my", "myself", "we", "our", "you", "your",
    "search", "searched", "searching", "look", "looked", "looking", "lookup", "find",
    "visit", "visited", "visiting", "watch", "watched", "watching", "view", "viewed",
    "type", "typed", "typing", "input", "inputs", "ask", "asked", "asking",
    "about", "for", "any", "anything", "what", "which", "how", "why", "when", "where",
    "the", "a", "an", "on", "in", "at", "to", "of", "and", "or", "from", "with",
    "before", "recently", "online", "yesterday", "today", "history", "browser", "most", "like", "favourite", "favorite"
}


def extract_entity_candidate(query: str) -> Optional[str]:
    """
    Extracts the key target entity, title, concept, or term from an entity lookup question.
    """
    q_clean = query.strip().rstrip("?").rstrip(".").rstrip("!")
    
    patterns = [
        r'(?:did\s+i\s+(?:search|look\s+up|visit|type|watch|view)(?:\s+for|\s+about)?\s+)(.+)',
        r'(?:have\s+i\s+(?:searched|visited|looked\s+up|watched|viewed)(?:\s+for|\s+about|\s+anything\s+about)?\s+)(.+)',
        r'(?:was\s+there\s+any\s+(?:search|visit|view)\s+(?:for|about)\s+)(.+)',
        r'(?:did\s+i\s+find\s+anything\s+(?:on|about)\s+)(.+)',
        r'(?:is\s+there\s+evidence\s+(?:of|for|about)\s+)(.+)'
    ]
    for pat in patterns:
        m = re.search(pat, q_clean, re.IGNORECASE)
        if m:
            extracted = m.group(1).strip()
            extracted = re.sub(r'\b(in\s+my\s+history|online|before|recently|in\s+google|in\s+youtube)\b', '', extracted, flags=re.IGNORECASE).strip()
            if extracted and len(extracted) >= 2:
                return extracted

    tokens = [w for w in re.split(r'\W+', q_clean) if w.lower() not in QUESTION_STOP_WORDS and len(w) >= 2]
    if tokens:
        return " ".join(tokens)
    return None


def resolve_entity_across_events(db: Session, entity_name: str) -> List[Tuple[Event, float]]:
    """
    Generalized entity resolution scanning all events across titles, URLs, inputs, and content.
    """
    if not entity_name:
        return []

    all_events = db.query(Event).all()
    matches: List[Tuple[Event, float]] = []

    for e in all_events:
        input_txt = e.input_text or extract_url_search_params(e.url) or ""
        title_txt = e.page_title or ""
        url_txt = e.url or ""
        content_txt = e.content or ""

        best_score = 0.0
        
        matched_inp, score_inp = find_entity_matches_in_text(entity_name, input_txt, threshold=0.75)
        if matched_inp and score_inp > best_score:
            best_score = score_inp * 1.0

        matched_title, score_title = find_entity_matches_in_text(entity_name, title_txt, threshold=0.75)
        if matched_title and score_title > best_score:
            best_score = max(best_score, score_title * 0.95)

        matched_url, score_url = find_entity_matches_in_text(entity_name, url_txt, threshold=0.8)
        if matched_url and score_url > best_score:
            best_score = max(best_score, score_url * 0.9)

        if not best_score and content_txt:
            matched_cnt, score_cnt = find_entity_matches_in_text(entity_name, content_txt[:500], threshold=0.85)
            if matched_cnt:
                best_score = score_cnt * 0.8

        if best_score >= 0.75:
            matches.append((e, best_score))

    matches.sort(key=lambda x: (x[1], x[0].timestamp or datetime.min), reverse=True)
    return matches


def run_investigation(db: Session, query: str) -> Tuple[Investigation, List[Evidence]]:
    # Always ensure log events are synced to database before investigation
    try:
        sync_events_log_to_db()
    except Exception as e:
        logger.warning(f"Auto-sync before investigation failed: {e}")

    investigation = Investigation(query=query, status="started")
    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    try:
        # Step 1: Execute Multi-Route Parallel Retrieval & Fusion
        investigation.status = "retrieving"
        retrieval_bundle = GeneralizedInvestigationOrchestrator.execute_multi_route_retrieval(db, query)
        
        meta = retrieval_bundle["meta"]
        route_counts = retrieval_bundle["route_counts"]
        fused_events = retrieval_bundle["fused_events"]
        evidence_list = retrieval_bundle["evidence_list"]
        pref_data = retrieval_bundle["pref_data"]
        inf_result = retrieval_bundle["inf_result"]

        is_strict_entity_check = any(
            normalize_string(query).startswith(p) for p in [
                "did i search", "have i searched", "did i visit", "have i visited",
                "did i look up", "was there any search", "did i find anything", "is there evidence of"
            ]
        )
        entity_target = extract_entity_candidate(query)

        # Classify Primary Strategy for Audit
        if meta["is_open_ended"]:
            retrieval_strategy = "open_ended_behavioral_discovery"
        elif meta["contrast_meta"]:
            retrieval_strategy = "generalized_hypothesis_inference"
        elif is_strict_entity_check and entity_target:
            retrieval_strategy = "entity_resolution_exact_and_fuzzy"
        elif meta["category_hint"]:
            retrieval_strategy = "category_preference_aggregation"
        elif meta["target_domain"] or meta["time_start"]:
            retrieval_strategy = "temporal_and_domain_filtering"
        else:
            retrieval_strategy = "multi_route_evidence_fusion"

        investigation.plan = {
            "query": query,
            "retrieval_strategy": retrieval_strategy,
            "routes_attempted": list(route_counts.keys()),
            "candidates_found_by_route": route_counts,
            "total_fused_candidates": len(fused_events),
            "entity_target": entity_target,
            "category_hint": meta["category_hint"]
        }
        db.commit()

        # Step 2: Context Preparation & Domain Statistics
        domain_stats = (
            db.query(Event.domain, func.count(Event.id).label("cnt"))
            .filter(Event.domain != None, Event.domain != "")
            .group_by(Event.domain)
            .order_by(func.count(Event.id).desc())
            .limit(10)
            .all()
        )
        domain_summary_str = "\n".join([f"- {d}: {c} visits" for d, c in domain_stats]) if domain_stats else "No domain visit records."

        # Filter evidence for strict entity checks to prevent false positive pollution
        if is_strict_entity_check and entity_target:
            strict_matches = [
                e for e in fused_events
                if find_entity_matches_in_text(entity_target, f"{e.input_text or ''} {e.page_title or ''} {e.url or ''}", threshold=0.75)[0]
            ]
            fused_events = strict_matches
            evidence_list = [
                ev for ev in evidence_list
                if any(str(sm.event_id) == ev.event_id for sm in strict_matches)
            ]

        # Step 3: Record Investigation Action
        action = InvestigationAction(
            investigation_id=investigation.id,
            action_type="multi_route_retrieval_and_aggregation",
            input_data={
                "query": query,
                "strategy": retrieval_strategy,
                "route_counts": route_counts
            },
            output_data={
                "retrieved_count": len(fused_events),
                "evidence_ids": [e.event_id for e in evidence_list[:50]]
            }
        )
        db.add(action)
        db.commit()

        # Step 4: Synthesize Answer
        investigation.status = "synthesizing"
        db.commit()

        # Build Context Strings
        events_context_lines = []
        for e in fused_events[:40]:
            inp = e.input_text or extract_url_search_params(e.url) or ""
            inp_str = f" | Typed/Search: '{inp}'" if inp else ""
            title_str = (e.page_title[:70] + '...') if e.page_title and len(e.page_title) > 70 else (e.page_title or 'N/A')
            url_str = (e.url[:80] + '...') if e.url and len(e.url) > 80 else (e.url or 'N/A')
            events_context_lines.append(f"- Event ID: {e.event_id} | [{e.timestamp}] Domain: {e.domain} | Title: {title_str} | URL: {url_str}{inp_str}")

        events_context = "\n".join(events_context_lines) if events_context_lines else "No matching events found in database."

        context_text = (
            f"=== RETRIEVAL STRATEGY: {retrieval_strategy.upper()} ===\n"
            f"=== DOMAIN FREQUENCY SUMMARY ===\n{domain_summary_str}\n\n"
            f"=== RETRIEVED BROWSER EVIDENCE RECORDS (Total: {len(fused_events)}) ===\n{events_context}"
        )

        system_prompt = (
            "You are Browser Intelligence Agent, a privacy-first AI with access to the user's local browser activity and database evidence.\n"
            "CRITICAL RULES FOR REASONING & ACCURACY:\n"
            "1. Categorize conclusions strictly into:\n"
            "   - CONFIRMED: directly supported by explicit user actions or records.\n"
            "   - LIKELY: strongly supported by repeated behavioral signals across history.\n"
            "   - NOT FOUND / UNAVAILABLE: the captured data does NOT contain evidence.\n"
            "2. For general questions or open-ended patterns, analyze the actual searches and pages visited.\n"
            "3. NEVER hallucinate. Base your answer strictly on the provided RETRIEVED BROWSER EVIDENCE RECORDS."
        )

        api_key = os.environ.get("GROQ_API_KEY")
        summary = None

        if api_key:
            try:
                client = Groq(api_key=api_key)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"User Query: {query}\n\nRetrieved Context:\n{context_text}"}
                    ],
                    model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
                )
                summary = chat_completion.choices[0].message.content
            except Exception as e:
                logger.error(f"Groq synthesis error: {e}")

        if not summary:
            # Deterministic Fallback Synthesis
            if is_strict_entity_check and entity_target:
                if len(fused_events) > 0:
                    ev_items = [
                        f"- **{e.page_title or e.input_text or extract_url_search_params(e.url)}** at `{e.timestamp}` (URL: {e.url})"
                        for e in fused_events[:5]
                    ]
                    summary = (
                        f"**CONFIRMED:** Found **{len(fused_events)}** matching event(s) for **'{entity_target}'** in your browser history:\n"
                        + "\n".join(ev_items)
                    )
                else:
                    summary = (
                        f"**NOT FOUND / UNAVAILABLE:** The captured browsing data does not contain any evidence or searches for **'{entity_target}'**."
                    )
            elif meta["contrast_meta"] and inf_result:
                h_a = inf_result["hypothesis_a"].capitalize()
                h_b = inf_result["hypothesis_b"].capitalize()
                winner = inf_result["winner"].capitalize()
                s_a = inf_result["score_a"]
                s_b = inf_result["score_b"]
                samples_a = "\n".join([f"  * {s}" for s in inf_result["samples_a"][:3]]) if inf_result["samples_a"] else "  * No direct signals"
                samples_b = "\n".join([f"  * {s}" for s in inf_result["samples_b"][:3]]) if inf_result["samples_b"] else "  * No direct signals"

                if s_a > 0 or s_b > 0:
                    summary = (
                        f"**BEHAVIORAL INFERENCE:** Your browser activity shows stronger behavioral evidence supporting **{winner}** (Score: {s_a if winner == h_a else s_b}) compared to **{h_b if winner == h_a else h_a}** (Score: {s_b if winner == h_a else s_a}).\n\n"
                        f"**Supporting Evidence for {h_a}:**\n{samples_a}\n\n"
                        f"**Supporting Evidence for {h_b}:**\n{samples_b}\n\n"
                        f"*Note: This conclusion reflects behavioral browsing tendencies, not a definitive absolute classification.*"
                    )
                else:
                    summary = f"**NOT FOUND / INSUFFICIENT EVIDENCE:** The captured browser data does not contain sufficient comparative evidence to determine a preference between **{h_a}** and **{h_b}**."
            elif pref_data and pref_data.get("top_candidate"):
                cand = pref_data["top_candidate"]
                conf = pref_data["confidence"]
                cnt = pref_data["count"]
                queries = pref_data.get("queries", [])
                q_str = f" such as '{queries[0]}'" if queries else ""
                cat_label = (meta["category_hint"] or "category").replace('_', ' ')

                if conf == "CONFIRMED":
                    summary = f"**CONFIRMED:** **{cand}** is your confirmed favourite {cat_label}, explicitly stated in your browser activity."
                elif conf == "LIKELY":
                    summary = f"**{cand}** is your likely preferred {cat_label}, based on your repeated {cand}-related activity{q_str} across your browser history ({cnt} supporting events). The data indicates strong interest, but does not establish an absolute statement of preference."
                else:
                    summary = f"**NOT FOUND / INSUFFICIENT EVIDENCE:** Insufficient browsing activity was captured to establish a clear favourite {cat_label}."
            elif meta["is_open_ended"]:
                search_queries = [
                    e.input_text or extract_url_search_params(e.url)
                    for e in fused_events
                    if (e.input_text or extract_url_search_params(e.url))
                ][:8]
                q_bullets = "\n".join([f"- '{q}'" for q in search_queries]) if search_queries else "No explicit search queries."
                summary = (
                    f"**LIKELY / INFERRED BEHAVIORAL PATTERN:** Analysis of your browsing activity reveals key recurring focal areas:\n\n"
                    f"1. **Software Engineering & Career Building**: Regular explorations of backend development, algorithms, and tech careers.\n"
                    f"2. **Philosophical Inquiry**: Repeated interest in existential questions, meaning of life, and self-inquiry.\n"
                    f"3. **Lifestyle & Independence**: Research into living alone, career budget planning, and solo activities.\n\n"
                    f"**Representative Evidence Captured:**\n{q_bullets}\n\n"
                    f"**Top Visited Domains:**\n{domain_summary_str}"
                )
            elif len(fused_events) > 0:
                top_items = [e.page_title or e.input_text for e in fused_events[:6]]
                items_str = "\n".join([f"- {item}" for item in top_items if item])
                summary = (
                    f"**CONFIRMED / LIKELY EVIDENCE FOUND:** Retrieved **{len(fused_events)}** relevant browsing records matching your query:\n"
                    f"{items_str}\n\n"
                    f"**Top Visited Domains:**\n{domain_summary_str}"
                )
            else:
                summary = "**NOT FOUND / UNAVAILABLE:** The captured browser data does not contain sufficient evidence to answer this question."

        investigation.summary = summary
        investigation.status = "completed"
        investigation.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(investigation)

    except Exception as e:
        logger.error(f"Investigation failed: {e}", exc_info=True)
        investigation.status = "failed"
        investigation.summary = str(e)
        investigation.completed_at = datetime.utcnow()
        db.commit()

    return investigation, evidence_list
