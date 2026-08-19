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
from services.preference import (
    detect_preference_category,
    infer_programming_preference,
    infer_comedian_preference,
    infer_entertainment_preference
)
from groq import Groq

logger = logging.getLogger(__name__)


def analyze_query_intent(query: str) -> Dict[str, Any]:
    q_lower = query.lower()
    
    is_input_search = any(k in q_lower for k in ["type", "typed", "search", "searched", "input", "query", "queries", "look up", "looking up", "ask", "asked"])
    is_ecommerce = any(k in q_lower for k in ["buy", "bought", "purchase", "purchased", "amazon", "cart", "order", "checkout"])
    is_bulk = any(k in q_lower for k in ["all", "everything", "every", "list all", "full list"])
    is_frequency = any(k in q_lower for k in ["most", "visit", "daily", "frequently", "top sites", "top websites"])
    pref_category = detect_preference_category(query)
    
    target_domain = None
    if "stack overflow" in q_lower or "stackoverflow" in q_lower:
        target_domain = "stackoverflow.com"
    elif "google" in q_lower:
        target_domain = "google.com"
    elif "youtube" in q_lower:
        target_domain = "youtube.com"
    elif "amazon" in q_lower:
        target_domain = "amazon.in"
    elif "github" in q_lower:
        target_domain = "github.com"
    else:
        domain_match = re.search(r'\b([a-z0-9\-]+\.(?:com|org|net|io|in|edu|gov))\b', q_lower)
        if domain_match:
            target_domain = domain_match.group(1)

    time_start = None
    time_end = None
    if "yesterday" in q_lower:
        now = datetime.utcnow()
        time_end = now
        time_start = now - timedelta(days=2)
    elif "today" in q_lower:
        now = datetime.utcnow()
        time_start = now - timedelta(days=1)

    limit = 500 if is_bulk else 50

    return {
        "is_input_search": is_input_search,
        "is_ecommerce": is_ecommerce,
        "is_bulk": is_bulk,
        "is_frequency": is_frequency,
        "pref_category": pref_category,
        "target_domain": target_domain,
        "time_start": time_start,
        "time_end": time_end,
        "limit": limit
    }


def run_investigation(db: Session, query: str) -> Tuple[Investigation, List[Evidence]]:
    investigation = Investigation(query=query, status="started")
    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    try:
        # Step 1: Analyze Intent & Plan
        intent = analyze_query_intent(query)
        pref_category = intent["pref_category"]

        investigation.status = "analyzing"
        investigation.plan = {
            "intent": intent,
            "preference_category": pref_category,
            "steps": ["Query intent analysis", "Preference signal extraction", "Database retrieval", "RRF Hybrid fallback", "LLM Synthesis"]
        }
        db.commit()

        # Step 2: Information Retrieval & Preference Signal Aggregation
        investigation.status = "retrieving"
        db.commit()

        db_query = db.query(Event)

        if intent["target_domain"]:
            db_query = db_query.filter(Event.domain.ilike(f"%{intent['target_domain']}%"))

        if intent["is_input_search"]:
            db_query = db_query.filter(
                or_(
                    and_(Event.input_text != None, Event.input_text != ""),
                    Event.event_type.in_(["search_submitted", "input_submitted", "form_submitted"]),
                    Event.url.ilike("%q=%"),
                    Event.url.ilike("%query=%"),
                    Event.url.ilike("%search=%")
                )
            )

        if intent["is_ecommerce"]:
            db_query = db_query.filter(
                or_(
                    Event.domain.ilike("%amazon%"),
                    Event.page_title.ilike("%order%"),
                    Event.page_title.ilike("%cart%"),
                    Event.page_title.ilike("%buy%"),
                    Event.page_title.ilike("%purchase%"),
                    Event.input_text.ilike("%buy%")
                )
            )

        if intent["time_start"]:
            db_query = db_query.filter(Event.timestamp >= intent["time_start"])
        if intent["time_end"]:
            db_query = db_query.filter(Event.timestamp <= intent["time_end"])

        # Fetch matching DB events
        exact_events = db_query.order_by(Event.timestamp.desc()).limit(intent["limit"]).all()

        # Run hybrid search for broader semantics
        search_res = search_hybrid(db, query, limit=15)
        top_uids = search_res.get("top_results", [])
        hybrid_events = db.query(Event).filter(Event.event_id.in_(top_uids)).all() if top_uids else []

        # Run Preference Inference if category detected
        pref_info = None
        pref_events: List[Event] = []
        if pref_category == "programming_language":
            pref_info, pref_events = infer_programming_preference(db)
        elif pref_category == "comedian":
            pref_info, pref_events = infer_comedian_preference(db)
        elif pref_category in ["movies_entertainment", "topics_interests", "general_preference"]:
            pref_info, pref_events = infer_entertainment_preference(db)

        # Combine all events, preserving deduplicated order
        seen_ids = set()
        combined_events: List[Event] = []

        for e in pref_events:
            if str(e.event_id) not in seen_ids:
                seen_ids.add(str(e.event_id))
                combined_events.append(e)

        for e in exact_events:
            if str(e.event_id) not in seen_ids:
                seen_ids.add(str(e.event_id))
                combined_events.append(e)

        for e in hybrid_events:
            if str(e.event_id) not in seen_ids:
                seen_ids.add(str(e.event_id))
                combined_events.append(e)

        # Domain visits count summary
        domain_stats = (
            db.query(Event.domain, func.count(Event.id).label("cnt"))
            .filter(Event.domain != None, Event.domain != "")
            .group_by(Event.domain)
            .order_by(func.count(Event.id).desc())
            .limit(10)
            .all()
        )

        domain_summary_str = "\n".join([f"- {d}: {c} visits" for d, c in domain_stats]) if domain_stats else "No domain visit records."

        # Target domain specific stats if requested
        target_domain_total = 0
        if intent["target_domain"]:
            target_domain_total = db.query(Event).filter(Event.domain.ilike(f"%{intent['target_domain']}%")).count()

        # Build Evidences List
        evidence_list: List[Evidence] = []
        for e in combined_events:
            inp = e.input_text or extract_url_search_params(e.url) or ""
            snippet = f"[{e.event_type}] Domain: {e.domain} | Title: {e.page_title or 'N/A'}"
            if inp:
                snippet += f" | Input/Search: '{inp}'"

            evidence_list.append(
                Evidence(
                    event_id=str(e.event_id),
                    timestamp=e.timestamp,
                    url=e.url,
                    title=e.page_title,
                    snippet=snippet,
                    relevance=1.0 if inp else 0.8
                )
            )

        # Build Preference Analysis Block for LLM Context
        pref_context_str = ""
        if pref_info and pref_info.get("top_candidate"):
            pref_context_str = (
                f"=== PREFERENCE INFERENCE ANALYSIS ===\n"
                f"Category: {pref_category}\n"
                f"Top Dynamically Discovered Candidate: {pref_info['top_candidate']}\n"
                f"Supporting Signals Count across Browser History: {pref_info['count']}\n"
                f"Confidence Classification: {pref_info['confidence']}\n"
                f"Captured Search Queries: {pref_info.get('queries', [])}\n"
                f"Top Candidate Breakdown: {pref_info.get('all_candidates', {})}\n\n"
            )

        # Build Compact Context for LLM
        events_context_lines = []
        for e in combined_events[:50]:
            inp = e.input_text or extract_url_search_params(e.url) or ""
            inp_str = f" | Typed/Search: '{inp}'" if inp else ""
            title_str = (e.page_title[:80] + '...') if e.page_title and len(e.page_title) > 80 else (e.page_title or 'N/A')
            url_str = (e.url[:90] + '...') if e.url and len(e.url) > 90 else (e.url or 'N/A')
            events_context_lines.append(f"- Event ID: {e.event_id} | [{e.timestamp}] Domain: {e.domain} | Type: {e.event_type} | Title: {title_str} | URL: {url_str}{inp_str}")

        events_context = "\n".join(events_context_lines) if events_context_lines else "No specific events matching criteria."

        context_text = (
            f"=== USER QUERY INTENT ===\n"
            f"Target Domain Filter: {intent['target_domain'] or 'None'} (Total Visits in DB: {target_domain_total})\n"
            f"Preference Category: {pref_category or 'None'}\n\n"
            f"{pref_context_str}"
            f"=== DOMAIN FREQUENCY SUMMARY ===\n{domain_summary_str}\n\n"
            f"=== RETRIEVED BROWSER EVIDENCE RECORDS (Total: {len(combined_events)}) ===\n{events_context}"
        )

        # Step 3: Action Record
        action = InvestigationAction(
            investigation_id=investigation.id,
            action_type="retrieval_and_filtering",
            input_data={"query": query, "intent": intent, "pref_category": pref_category},
            output_data={"retrieved_count": len(combined_events), "evidence_ids": [e.event_id for e in evidence_list]}
        )
        db.add(action)
        db.commit()

        # Step 4: LLM Synthesizer with Anti-Hallucination & Preference Guardrails
        investigation.status = "synthesizing"
        db.commit()

        system_prompt = (
            "You are Browser Intelligence Agent, a privacy-first AI with access to the user's local browser activity and database evidence.\n"
            "CRITICAL RULES FOR REASONING & PREFERENCE INFERENCE:\n"
            "1. Categorize conclusions strictly into:\n"
            "   - CONFIRMED: directly supported by explicit user statements.\n"
            "   - LIKELY: strongly supported by repeated browser signals across history.\n"
            "   - UNKNOWN / INSUFFICIENT EVIDENCE: missing or insufficient signals captured.\n"
            "2. DO NOT state an inference as an absolute fact. (Example GOOD response: 'Java is your likely favourite programming language, based on your repeated Java-related searches such as \"java 8 vs java 15\".')\n"
            "3. NEVER hardcode candidate names. Always state the entity dynamically discovered in the evidence.\n"
            "4. Base your answer strictly on the provided RETRIEVED BROWSER EVIDENCE RECORDS and PREFERENCE INFERENCE ANALYSIS."
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
                    model=os.environ.get("GROQ_MODEL", "groq/compound")
                )
                summary = chat_completion.choices[0].message.content
            except Exception as e:
                logger.error(f"Groq synthesis error: {e}")

        if not summary:
            # Deterministic Fallback Synthesis enforcing anti-hallucination & preference rules
            if pref_info and pref_info.get("top_candidate"):
                cand = pref_info["top_candidate"]
                conf = pref_info["confidence"]
                cnt = pref_info["count"]
                queries = pref_info.get("queries", [])
                q_str = f" such as '{queries[0]}'" if queries else ""

                if conf == "CONFIRMED":
                    summary = f"**CONFIRMED:** **{cand}** is your confirmed favourite {pref_category.replace('_', ' ')}, explicitly stated in your browser activity."
                elif conf == "LIKELY":
                    summary = f"**{cand}** is your likely favourite {pref_category.replace('_', ' ')}, based on your repeated {cand}-related searches{q_str} and browsing activity across your browser history (supporting signals: {cnt}). The data indicates strong preference, but does not establish an absolute statement of preference."
                else:
                    summary = f"**UNKNOWN / INSUFFICIENT EVIDENCE:** Insufficient browsing activity was captured to establish a clear favourite {pref_category.replace('_', ' ')}."
            elif intent["target_domain"]:
                input_events = [e for e in combined_events if (e.input_text or extract_url_search_params(e.url))]
                if input_events:
                    queries_list = "\n".join([f"- '{e.input_text or extract_url_search_params(e.url)}' (at {e.timestamp})" for e in input_events])
                    summary = (
                        f"**CONFIRMED:** Found {len(input_events)} captured search/typed inputs on **{intent['target_domain']}**:\n{queries_list}\n\n"
                        f"**VISIT COUNTS:** Total visits recorded to {intent['target_domain']}: **{target_domain_total}**."
                    )
                else:
                    summary = (
                        f"**CONFIRMED:** Total visits to **{intent['target_domain']}**: **{target_domain_total}**.\n\n"
                        f"**UNKNOWN / UNAVAILABLE:** You visited {intent['target_domain']} {target_domain_total} times, but no search queries, typed inputs, or form submissions were captured for {intent['target_domain']} in your browsing data."
                    )
            else:
                summary = f"**BROWSER ACTIVITY SUMMARY:**\nTop Visited Domains:\n{domain_summary_str}\n\nRecent Activity Events:\n{events_context}"

        investigation.summary = summary
        investigation.status = "completed"
        investigation.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(investigation)

    except Exception as e:
        investigation.status = "failed"
        investigation.summary = str(e)
        investigation.completed_at = datetime.utcnow()
        db.commit()

    return investigation, evidence_list
