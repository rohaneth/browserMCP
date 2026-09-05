from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.events import Event
from models.sessions import BrowserSession
from services.clustering import InterestClusterEngine
from services.anomaly_detection import BehavioralAnomalyDetector
from services.recommendation import RecommendationEngine
from utils.normalization import extract_url_search_params


class WellbeingAnalyticsService:
    """
    Computes comprehensive Digital Wellbeing, Focus & Productivity, Behavioral Analytics,
    and Interest Evolution metrics directly from active browser history in the database.
    """

    @classmethod
    def get_full_wellbeing_metrics(cls, db: Session) -> Dict[str, Any]:
        events = db.query(Event).order_by(Event.timestamp.asc()).all()
        sessions = db.query(BrowserSession).order_by(BrowserSession.start_time.asc()).all()

        if not events:
            return cls._empty_metrics()

        # 1. Overview & Heatmap Calculations
        total_events = len(events)
        searches_count = 0
        domains_counter = Counter()
        hourly_counter = Counter()
        daily_counter = Counter()
        heatmap = defaultdict(lambda: [0] * 24)  # day_of_week (0=Mon..6=Sun) -> 24 hours

        for e in events:
            if not e.timestamp:
                continue
            dt = e.timestamp
            hourly_counter[dt.hour] += 1
            day_str = dt.strftime("%Y-%m-%d")
            daily_counter[day_str] += 1
            heatmap[dt.weekday()][dt.hour] += 1

            if e.domain:
                domains_counter[e.domain.lower()] += 1

            inp = e.input_text or extract_url_search_params(e.url)
            if inp or e.event_type == "search_submitted":
                searches_count += 1

        top_domains = [{"domain": d, "count": c} for d, c in domains_counter.most_common(8)]
        most_active_hours = [{"hour": f"{h:02d}:00", "count": hourly_counter[h]} for h in range(24)]
        daily_trends = [{"date": d, "count": daily_counter[d]} for d in sorted(daily_counter.keys())]

        # 2. Session & Time Metrics
        total_browsing_minutes = 0.0
        deep_work_sessions = 0
        doomscroll_sessions = 0
        longest_session_minutes = 0.0
        session_durations = []

        categorized_sessions = []
        for s in sessions:
            if not s.start_time or not s.end_time:
                continue
            dur = (s.end_time - s.start_time).total_seconds() / 60.0
            total_browsing_minutes += dur
            session_durations.append(dur)
            if dur > longest_session_minutes:
                longest_session_minutes = dur

            # Inspect events inside session window
            s_events = [e for e in events if s.start_time <= e.timestamp <= s.end_time]
            s_domains = Counter([e.domain for e in s_events if e.domain])
            top_dom = s_domains.most_common(1)[0][0] if s_domains else "web"

            # Classification of session
            session_type = "general"
            if dur >= 20 and any(d in ["github.com", "spring.io", "stackoverflow.com", "notion.so", "google.com"] for d in s_domains):
                deep_work_sessions += 1
                session_type = "deep_work"
            elif any("instagram.com" in d or "youtube.com" in d for d in s_domains) and len(s_events) >= 20:
                doomscroll_sessions += 1
                session_type = "doomscrolling"

            categorized_sessions.append({
                "id": str(s.id),
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
                "duration_minutes": round(dur, 1),
                "event_count": s.event_count or len(s_events),
                "top_domain": top_dom,
                "session_type": session_type
            })

        # 3. Focus, Productivity & Attention Fragmentation Scores
        # Context switch frequency: when domain changes between consecutive events
        context_switches = 0
        for i in range(1, len(events)):
            if events[i].domain and events[i-1].domain and events[i].domain != events[i-1].domain:
                context_switches += 1

        switch_rate = context_switches / max(total_events, 1)
        
        # Focus Score: High when long sessions & low rapid switching (0 - 100)
        focus_score = max(10, min(95, int(100 - (switch_rate * 45) - (doomscroll_sessions * 8) + (deep_work_sessions * 7))))
        
        # Productivity Score: ratio of dev/study/reference domains vs social/short-form
        work_domains = {"github.com", "spring.io", "stackoverflow.com", "notion.so", "docs.google.com", "electronicshub.org", "tutorialspoint.com", "geeksforgeeks.org", "nptel.ac.in", "cmu.edu", "stanford.edu", "modelcontextprotocol.io", "langchain-ai.github.io", "qdrant.tech", "openai.com"}
        social_domains = {"instagram.com", "youtube.com", "reddit.com", "tiktok.com"}
        
        work_events = sum(1 for e in events if e.domain and any(wd in e.domain for wd in work_domains))
        social_events = sum(1 for e in events if e.domain and any(sd in e.domain for sd in social_domains))
        
        productivity_score = max(15, min(98, int((work_events / max(work_events + social_events, 1)) * 100)))
        attention_fragmentation_score = int(min(95, max(10, switch_rate * 100)))

        # 4. Late Night & Sleep Hygiene Analysis (12:00 AM - 04:00 AM)
        late_night_events = [e for e in events if e.timestamp and (0 <= e.timestamp.hour < 4)]
        late_night_count = len(late_night_events)
        late_night_ratio = round(late_night_count / max(total_events, 1), 3)
        sleep_hygiene_score = max(10, int(100 - (late_night_ratio * 180)))
        healthy_usage_score = int((focus_score * 0.4) + (productivity_score * 0.3) + (sleep_hygiene_score * 0.3))

        # 5. Behavioral Analytics & Curiosity Ratio
        unique_domains_count = len(domains_counter)
        exploration_ratio = round(unique_domains_count / max(total_events / 15, 1), 2)
        curiosity_score = min(98, int(exploration_ratio * 35 + searches_count * 0.5))

        # 6. Interest Evolution & Clusters
        clusters = InterestClusterEngine.discover_clusters(db, n_clusters=5)
        clusters_data = [
            {
                "cluster_id": c.cluster_id,
                "label": c.label,
                "top_keywords": c.top_keywords,
                "coherence_score": round(c.coherence_score, 2)
            }
            for c in clusters
        ]

        # 7. Anomalies from Isolation Forest
        anomalies = BehavioralAnomalyDetector.detect_anomalies(db, contamination=0.05, limit=6)
        anomalies_data = [
            {
                "event_id": a.event_id,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                "anomaly_score": round(a.anomaly_score, 3),
                "reasons": a.anomaly_reasons,
                "unusual_dimensions": a.unusual_dimensions
            }
            for a in anomalies
        ]

        # 8. Learning & Content Recommendations
        recs = RecommendationEngine.get_recommendations(db, limit=5)
        recs_data = [
            {
                "topic": r.topic,
                "category": r.category,
                "relevance_score": round(r.relevance_score, 3),
                "rationale": r.rationale
            }
            for r in recs
        ]

        # 9. Wellbeing Suggestions & Improvement Tips
        suggestions = []
        if doomscroll_sessions > 0:
            suggestions.append("High-velocity short-form media sessions detected. Consider setting a 15-minute timer before opening social feeds.")
        if late_night_count > 5:
            suggestions.append(f"Detected {late_night_count} events past midnight. Blue-light exposure after 12 AM disrupts melatonin production.")
        if context_switches > 50:
            suggestions.append("Frequent context switching observed. Batching browser tasks into designated 25-minute Pomodoro intervals will boost focus.")
        if deep_work_sessions > 0:
            suggestions.append("Great sustained deep work sessions in engineering and research topics.")

        return {
            "overview": {
                "total_events": total_events,
                "total_browsing_minutes": round(total_browsing_minutes, 1),
                "total_sessions": len(sessions),
                "total_searches": searches_count,
                "top_domains": top_domains,
                "most_active_hours": most_active_hours,
                "daily_trends": daily_trends,
                "heatmap": heatmap
            },
            "focus_and_productivity": {
                "focus_score": focus_score,
                "productivity_score": productivity_score,
                "attention_fragmentation_score": attention_fragmentation_score,
                "deep_work_sessions_count": deep_work_sessions,
                "doomscroll_sessions_count": doomscroll_sessions,
                "context_switches_count": context_switches,
                "longest_uninterrupted_minutes": round(longest_session_minutes, 1),
                "recent_sessions": categorized_sessions[-10:]
            },
            "behavioral_analytics": {
                "exploration_vs_exploitation_ratio": exploration_ratio,
                "curiosity_score": curiosity_score,
                "work_events_count": work_events,
                "social_events_count": social_events
            },
            "digital_wellbeing": {
                "healthy_usage_score": healthy_usage_score,
                "sleep_hygiene_score": sleep_hygiene_score,
                "late_night_events_count": late_night_count,
                "suggestions": suggestions
            },
            "interest_evolution": {
                "clusters": clusters_data,
                "diversity_score": min(95, int(len(clusters_data) * 18 + unique_domains_count * 0.5))
            },
            "anomalies": anomalies_data,
            "recommendations": recs_data
        }

    @classmethod
    def _empty_metrics(cls) -> Dict[str, Any]:
        return {
            "overview": {"total_events": 0, "total_browsing_minutes": 0, "total_sessions": 0, "total_searches": 0, "top_domains": [], "most_active_hours": [], "daily_trends": [], "heatmap": {}},
            "focus_and_productivity": {"focus_score": 0, "productivity_score": 0, "attention_fragmentation_score": 0, "deep_work_sessions_count": 0, "doomscroll_sessions_count": 0, "context_switches_count": 0, "longest_uninterrupted_minutes": 0, "recent_sessions": []},
            "behavioral_analytics": {"exploration_vs_exploitation_ratio": 0, "curiosity_score": 0, "work_events_count": 0, "social_events_count": 0},
            "digital_wellbeing": {"healthy_usage_score": 0, "sleep_hygiene_score": 0, "late_night_events_count": 0, "suggestions": []},
            "interest_evolution": {"clusters": [], "diversity_score": 0},
            "anomalies": [],
            "recommendations": []
        }
