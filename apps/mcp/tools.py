import sys
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../api')))

from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc
from db.session import SessionLocal
from models.events import Event
from models.sessions import BrowserSession
from services.investigation import run_investigation
from services.search import search_events, search_hybrid
from services.preference import (
    infer_programming_preference,
    infer_comedian_preference,
    infer_entertainment_preference,
    detect_preference_category
)
from services.sessions import assign_unassigned_events_to_sessions
from utils.privacy import sanitize_text, sanitize_metadata
from utils.normalization import extract_url_search_params


def parse_flexible_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """
    Parses ISO strings, dates (YYYY-MM-DD), timestamps or relative keywords.
    """
    if not dt_str:
        return None
    dt_str = dt_str.strip()
    if not dt_str:
        return None

    # Handle standard ISO formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            pass

    # Try dateutil parser if available
    try:
        from dateutil import parser
        return parser.parse(dt_str)
    except Exception:
        pass

    return None


def get_db_session() -> Session:
    return SessionLocal()


def execute_investigate(question: str) -> Dict[str, Any]:
    """
    Main general-purpose tool for arbitrary/complex questions.
    Uses multi-signal retrieval, dynamic candidate inference, anti-hallucination guardrails,
    and returns categorized conclusions (CONFIRMED / LIKELY / UNKNOWN) with evidence IDs.
    """
    db = get_db_session()
    try:
        try:
            from services.sync_log import sync_events_log_to_db
            sync_events_log_to_db()
        except Exception:
            pass

        # Ensure sessionization is up to date
        try:
            assign_unassigned_events_to_sessions(db)
        except Exception:
            pass

        investigation, evidence_list = run_investigation(db, question)
        
        # Serialize evidence with sanitized data
        evidences = [
            {
                "event_id": ev.event_id,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "url": ev.url,
                "title": sanitize_text(ev.title),
                "snippet": sanitize_text(ev.snippet),
                "relevance": ev.relevance
            }
            for ev in evidence_list
        ]

        return {
            "status": investigation.status,
            "question": question,
            "answer": sanitize_text(investigation.summary),
            "evidence_count": len(evidences),
            "evidence": evidences[:30],
            "plan": investigation.plan
        }
    finally:
        db.close()


def execute_search_history(
    query: str,
    domain: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Searches browser history using keyword and hybrid search across URLs, titles, search queries and content.
    """
    db = get_db_session()
    try:
        dt_start = parse_flexible_datetime(start_time)
        dt_end = parse_flexible_datetime(end_time)

        search_res = search_events(
            db=db,
            keyword=query,
            start_time=dt_start,
            end_time=dt_end,
            domain=domain,
            event_type=event_type
        )

        matched_events = []
        for ev in search_res.events[:limit]:
            matched_events.append({
                "event_id": str(ev.event_id),
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "event_type": ev.event_type,
                "domain": ev.domain,
                "url": ev.url,
                "page_title": sanitize_text(ev.page_title),
                "input_text": sanitize_text(ev.input_text),
                "content_preview": sanitize_text(ev.content[:200]) if ev.content else None,
                "session_id": str(ev.session_id) if ev.session_id else None
            })

        return {
            "query": query,
            "total_matches": search_res.total,
            "returned_count": len(matched_events),
            "events": matched_events
        }
    finally:
        db.close()


def execute_get_timeline(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    domain: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Returns a chronological sequence of browser events with timestamps, page titles, URLs, and inputs.
    """
    db = get_db_session()
    try:
        query = db.query(Event)
        dt_start = parse_flexible_datetime(start_time)
        dt_end = parse_flexible_datetime(end_time)

        if dt_start:
            query = query.filter(Event.timestamp >= dt_start)
        if dt_end:
            query = query.filter(Event.timestamp <= dt_end)
        if domain:
            query = query.filter(Event.domain.ilike(f"%{domain.lower()}%"))
        if event_type:
            query = query.filter(Event.event_type == event_type)

        total_count = query.count()
        events_db = query.order_by(desc(Event.timestamp), desc(Event.id)).offset(offset).limit(limit).all()

        timeline = []
        for ev in events_db:
            inp = ev.input_text or extract_url_search_params(ev.url)
            timeline.append({
                "event_id": str(ev.event_id),
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "event_type": ev.event_type,
                "domain": ev.domain,
                "page_title": sanitize_text(ev.page_title),
                "url": ev.url,
                "input_text": sanitize_text(inp) if inp else None,
                "session_id": str(ev.session_id) if ev.session_id else None
            })

        return {
            "total_count": total_count,
            "returned_count": len(timeline),
            "offset": offset,
            "limit": limit,
            "timeline": timeline
        }
    finally:
        db.close()


def execute_get_sessions(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 20,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves and analyzes browser sessions, calculating duration, visited websites,
    search queries, event counts, and dominant activities.
    """
    db = get_db_session()
    try:
        # Update any pending sessions
        assign_unassigned_events_to_sessions(db)

        dt_start = parse_flexible_datetime(start_time)
        dt_end = parse_flexible_datetime(end_time)

        query = db.query(BrowserSession)
        if session_id:
            query = query.filter(BrowserSession.id == session_id)
        if dt_start:
            query = query.filter(BrowserSession.start_time >= dt_start)
        if dt_end:
            query = query.filter(BrowserSession.end_time <= dt_end)

        sessions_db = query.order_by(desc(BrowserSession.start_time)).limit(limit).all()

        analyzed_sessions = []
        for sess in sessions_db:
            # Fetch events in this session
            events = db.query(Event).filter(Event.session_id == sess.id).order_by(Event.timestamp.asc()).all()
            
            domains = [e.domain for e in events if e.domain]
            domain_counts = dict(Counter(domains).most_common(5))
            
            searches = []
            pages_visited = []
            for e in events:
                inp = e.input_text or extract_url_search_params(e.url)
                if inp and inp not in searches:
                    searches.append(sanitize_text(inp))
                if e.page_title and e.page_title not in pages_visited:
                    pages_visited.append(sanitize_text(e.page_title[:80]))

            duration_seconds = max(0, int((sess.end_time - sess.start_time).total_seconds())) if sess.start_time and sess.end_time else 0
            
            # Identify dominant activity
            top_domain = list(domain_counts.keys())[0] if domain_counts else "Unknown"
            dominant_activity = f"Browsing on {top_domain}"
            if searches:
                dominant_activity += f" (Searched: {', '.join(searches[:2])})"

            analyzed_sessions.append({
                "session_id": str(sess.id),
                "start_time": sess.start_time.isoformat() if sess.start_time else None,
                "end_time": sess.end_time.isoformat() if sess.end_time else None,
                "duration_seconds": duration_seconds,
                "duration_human": f"{duration_seconds // 60}m {duration_seconds % 60}s" if duration_seconds >= 60 else f"{duration_seconds}s",
                "event_count": sess.event_count or len(events),
                "dominant_activity": dominant_activity,
                "top_domains": domain_counts,
                "searches": searches[:10],
                "sample_pages": pages_visited[:5]
            })

        return {
            "total_sessions": len(analyzed_sessions),
            "sessions": analyzed_sessions
        }
    finally:
        db.close()


def execute_get_domain_statistics(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 20,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes domain visit frequencies, distinct URLs visited, queries searched per domain,
    and first/last seen timestamps.
    """
    db = get_db_session()
    try:
        dt_start = parse_flexible_datetime(start_time)
        dt_end = parse_flexible_datetime(end_time)

        query = db.query(Event).filter(Event.domain != None, Event.domain != "")
        if dt_start:
            query = query.filter(Event.timestamp >= dt_start)
        if dt_end:
            query = query.filter(Event.timestamp <= dt_end)
        if domain:
            query = query.filter(Event.domain.ilike(f"%{domain.lower()}%"))

        events = query.all()

        domain_data: Dict[str, Dict[str, Any]] = {}
        for ev in events:
            dom = ev.domain.lower()
            if dom not in domain_data:
                domain_data[dom] = {
                    "domain": dom,
                    "event_count": 0,
                    "unique_urls": set(),
                    "queries": set(),
                    "first_seen": ev.timestamp,
                    "last_seen": ev.timestamp
                }

            entry = domain_data[dom]
            entry["event_count"] += 1
            if ev.url:
                entry["unique_urls"].add(ev.url)
            inp = ev.input_text or extract_url_search_params(ev.url)
            if inp:
                entry["queries"].add(sanitize_text(inp))
            if ev.timestamp and (not entry["first_seen"] or ev.timestamp < entry["first_seen"]):
                entry["first_seen"] = ev.timestamp
            if ev.timestamp and (not entry["last_seen"] or ev.timestamp > entry["last_seen"]):
                entry["last_seen"] = ev.timestamp

        sorted_domains = sorted(domain_data.values(), key=lambda x: x["event_count"], reverse=True)

        results = []
        for item in sorted_domains[:limit]:
            results.append({
                "domain": item["domain"],
                "total_events": item["event_count"],
                "unique_pages_count": len(item["unique_urls"]),
                "searches_conducted": list(item["queries"])[:10],
                "first_seen": item["first_seen"].isoformat() if item["first_seen"] else None,
                "last_seen": item["last_seen"].isoformat() if item["last_seen"] else None
            })

        return {
            "total_unique_domains": len(domain_data),
            "domains": results
        }
    finally:
        db.close()


def execute_compare_time_periods(
    period_a_start: str,
    period_a_end: str,
    period_b_start: str,
    period_b_end: str,
    label_a: str = "Period A",
    label_b: str = "Period B"
) -> Dict[str, Any]:
    """
    Compares browsing activities, domain frequencies, search counts, and session metrics between two time windows.
    """
    db = get_db_session()
    try:
        def get_stats_for_window(dt_s: datetime, dt_e: datetime) -> Dict[str, Any]:
            events = db.query(Event).filter(Event.timestamp >= dt_s, Event.timestamp <= dt_e).all()
            sessions = db.query(BrowserSession).filter(BrowserSession.start_time >= dt_s, BrowserSession.start_time <= dt_e).all()
            
            domains = [e.domain for e in events if e.domain]
            domain_counts = dict(Counter(domains).most_common(5))
            
            searches = set()
            for e in events:
                inp = e.input_text or extract_url_search_params(e.url)
                if inp:
                    searches.add(sanitize_text(inp))

            total_duration_sec = sum(
                max(0, int((s.end_time - s.start_time).total_seconds()))
                for s in sessions if s.start_time and s.end_time
            )

            return {
                "event_count": len(events),
                "session_count": len(sessions),
                "total_session_duration_minutes": round(total_duration_sec / 60.0, 1),
                "top_domains": domain_counts,
                "unique_searches_count": len(searches),
                "sample_searches": list(searches)[:5]
            }

        da_s = parse_flexible_datetime(period_a_start)
        da_e = parse_flexible_datetime(period_a_end)
        db_s = parse_flexible_datetime(period_b_start)
        db_e = parse_flexible_datetime(period_b_end)

        if not da_s or not da_e or not db_s or not db_e:
            raise ValueError("All period start and end dates must be valid parseable date strings.")

        stats_a = get_stats_for_window(da_s, da_e)
        stats_b = get_stats_for_window(db_s, db_e)

        return {
            "comparison": {
                label_a: {
                    "time_range": f"{da_s.isoformat()} to {da_e.isoformat()}",
                    **stats_a
                },
                label_b: {
                    "time_range": f"{db_s.isoformat()} to {db_e.isoformat()}",
                    **stats_b
                }
            },
            "summary_insights": {
                "events_delta": stats_a["event_count"] - stats_b["event_count"],
                "sessions_delta": stats_a["session_count"] - stats_b["session_count"],
                "primary_domain_a": list(stats_a["top_domains"].keys())[0] if stats_a["top_domains"] else None,
                "primary_domain_b": list(stats_b["top_domains"].keys())[0] if stats_b["top_domains"] else None
            }
        }
    finally:
        db.close()


def execute_infer_preferences(
    category: Optional[str] = None,
    query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs dynamic preference & interest inference across programming languages,
    comedians, entertainment, or general topics based on captured signals.
    """
    db = get_db_session()
    try:
        detected_category = category or (detect_preference_category(query) if query else "programming_language") or "programming_language"

        pref_info: Dict[str, Any] = {}
        events_list: List[Event] = []

        if detected_category == "programming_language":
            pref_info, events_list = infer_programming_preference(db)
        elif detected_category == "comedian":
            pref_info, events_list = infer_comedian_preference(db)
        elif detected_category in ["movies_entertainment", "topics_interests", "general_preference"]:
            pref_info, events_list = infer_entertainment_preference(db)
        else:
            pref_info, events_list = infer_programming_preference(db)

        top_candidate = pref_info.get("top_candidate")
        confidence = pref_info.get("confidence", "UNKNOWN")

        # Ground answer with anti-hallucination rules
        if top_candidate:
            if confidence == "CONFIRMED":
                narrative = f"CONFIRMED: {top_candidate} is your confirmed favorite {detected_category.replace('_', ' ')} based on explicit browser statements."
            elif confidence == "LIKELY":
                narrative = f"LIKELY: {top_candidate} is your likely favorite {detected_category.replace('_', ' ')}, supported by {pref_info.get('count', 0)} browser signals and queries."
            else:
                narrative = f"UNKNOWN / INSUFFICIENT EVIDENCE: Insufficient signals to confirm a favorite {detected_category.replace('_', ' ')}."
        else:
            narrative = f"UNKNOWN / INSUFFICIENT EVIDENCE: No {detected_category.replace('_', ' ')} preference signals found in browser data."

        evidences = [
            {
                "event_id": str(e.event_id),
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "domain": e.domain,
                "url": e.url,
                "page_title": sanitize_text(e.page_title),
                "input_text": sanitize_text(e.input_text or extract_url_search_params(e.url))
            }
            for e in events_list[:15]
        ]

        return {
            "category": detected_category,
            "top_candidate": top_candidate,
            "confidence": confidence,
            "narrative": narrative,
            "breakdown": pref_info.get("all_candidates", {}),
            "captured_queries": pref_info.get("queries", []),
            "supporting_evidence_count": len(events_list),
            "evidence": evidences
        }
    finally:
        db.close()


def execute_get_behavioral_patterns(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes user behavioral patterns: active hours of the day, weekday distribution,
    peak browsing time windows, and dominant interaction types.
    """
    db = get_db_session()
    try:
        dt_start = parse_flexible_datetime(start_time)
        dt_end = parse_flexible_datetime(end_time)

        query = db.query(Event)
        if dt_start:
            query = query.filter(Event.timestamp >= dt_start)
        if dt_end:
            query = query.filter(Event.timestamp <= dt_end)

        events = query.all()
        if not events:
            return {"total_events": 0, "message": "No events found in specified time range."}

        hourly_dist = {i: 0 for i in range(24)}
        day_dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0} # 0=Monday, 6=Sunday
        event_types = Counter()

        for ev in events:
            if ev.timestamp:
                hourly_dist[ev.timestamp.hour] += 1
                day_dist[ev.timestamp.weekday()] += 1
            if ev.event_type:
                event_types[ev.event_type] += 1

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_breakdown = {day_names[k]: v for k, v in day_dist.items()}

        peak_hour = max(hourly_dist.items(), key=lambda x: x[1])[0]
        peak_day = max(day_dist.items(), key=lambda x: x[1])[0]

        # Categorize peak period
        if 5 <= peak_hour < 12:
            time_of_day = "Morning (05:00 - 12:00)"
        elif 12 <= peak_hour < 17:
            time_of_day = "Afternoon (12:00 - 17:00)"
        elif 17 <= peak_hour < 22:
            time_of_day = "Evening (17:00 - 22:00)"
        else:
            time_of_day = "Night / Late Night (22:00 - 05:00)"

        return {
            "total_events_analyzed": len(events),
            "peak_hour_utc": f"{peak_hour:02d}:00",
            "peak_time_of_day": time_of_day,
            "peak_active_day": day_names[peak_day],
            "hourly_distribution": hourly_dist,
            "weekday_distribution": weekday_breakdown,
            "top_interaction_types": dict(event_types.most_common(5))
        }
    finally:
        db.close()


def execute_get_evidence(evidence_ids: List[str]) -> Dict[str, Any]:
    """
    Retrieves full details for specific event IDs or memory evidence references,
    providing complete verifiability and transparency without exposing sensitive raw secrets.
    """
    db = get_db_session()
    try:
        events = db.query(Event).filter(Event.event_id.in_(evidence_ids)).all()

        records = []
        for e in events:
            records.append({
                "event_id": str(e.event_id),
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "event_type": e.event_type,
                "domain": e.domain,
                "url": e.url,
                "page_title": sanitize_text(e.page_title),
                "input_text": sanitize_text(e.input_text or extract_url_search_params(e.url)),
                "content_excerpt": sanitize_text(e.content[:300]) if e.content else None,
                "metadata": sanitize_metadata(e.metadata_),
                "session_id": str(e.session_id) if e.session_id else None
            })

        return {
            "requested_count": len(evidence_ids),
            "found_count": len(records),
            "records": records
        }
    finally:
        db.close()
