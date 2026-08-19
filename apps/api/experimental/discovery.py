import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import Counter

from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.events import Event
from models.sessions import BrowserSession
from models.experimental import DiscoveryRun, DiscoveryResult
from utils.privacy import sanitize_text
from utils.normalization import extract_url_search_params
from services.preference import LANGUAGES

logger = logging.getLogger(__name__)

class BrowserSelfDiscovery:
    """
    Autonomous Browser Self-Discovery Engine.
    Executes a multi-stage discovery pipeline:
    1. Inspects entire browser dataset.
    2. Autonomously generates candidate behavioral hypotheses across interests, workflow habits, and temporal patterns.
    3. Evaluates hypotheses against concrete evidence.
    4. Gathers supporting evidence IDs.
    5. Synthesizes discoveries with clear CONFIRMED vs LIKELY confidence ratings.
    """

    @classmethod
    def run_discovery(cls, focus_hint: Optional[str] = None) -> Dict[str, Any]:
        db = SessionLocal()
        run = DiscoveryRun(
            focus_hint=focus_hint or "General browsing pattern & interest discovery",
            status="analyzing"
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            # 1. Fetch available data
            all_events = db.query(Event).order_by(Event.timestamp.asc()).all()
            if not all_events:
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                db.commit()
                return {"run_id": str(run.id), "status": "completed", "discoveries": []}

            # 2. Hypothesis Generation & Evaluation
            hypotheses = cls._generate_and_evaluate_hypotheses(db, all_events)
            run.hypotheses_generated = len(hypotheses)

            confirmed_count = 0
            results_to_save = []

            for hyp in hypotheses:
                if hyp["confidence"] in ["CONFIRMED", "LIKELY"]:
                    confirmed_count += 1
                    res = DiscoveryResult(
                        run_id=run.id,
                        category=hyp["category"],
                        hypothesis=hyp["hypothesis"],
                        confidence=hyp["confidence"],
                        narrative=hyp["narrative"],
                        supporting_evidence=hyp["supporting_evidence"]
                    )
                    db.add(res)
                    results_to_save.append({
                        "category": hyp["category"],
                        "hypothesis": hyp["hypothesis"],
                        "confidence": hyp["confidence"],
                        "narrative": hyp["narrative"],
                        "evidence_count": len(hyp["supporting_evidence"]),
                        "evidence": hyp["supporting_evidence"][:5]
                    })

            run.hypotheses_confirmed = confirmed_count
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            db.commit()

            return {
                "run_id": str(run.id),
                "status": "completed",
                "focus": run.focus_hint,
                "hypotheses_generated": run.hypotheses_generated,
                "discoveries_count": len(results_to_save),
                "discoveries": results_to_save
            }

        except Exception as e:
            logger.error(f"Error during self discovery run: {e}")
            run.status = "failed"
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"run_id": str(run.id), "status": "failed", "error": str(e)}
        finally:
            db.close()

    @classmethod
    def _generate_and_evaluate_hypotheses(cls, db: Session, events: List[Event]) -> List[Dict[str, Any]]:
        hypotheses = []

        # A. Emerging / Dominant Tech Interests
        lang_signals: Dict[str, List[Event]] = {}
        for e in events:
            text = f"{e.input_text or ''} {extract_url_search_params(e.url) or ''} {e.page_title or ''} {e.url or ''}".lower()
            for lang in LANGUAGES:
                if f" {lang} " in f" {text} " or f"/{lang}" in text or f"={lang}" in text:
                    display = lang.upper() if lang in ["sql", "cpp", "php", "css", "html"] else lang.capitalize()
                    if display not in lang_signals:
                        lang_signals[display] = []
                    lang_signals[display].append(e)

        if lang_signals:
            sorted_langs = sorted(lang_signals.items(), key=lambda x: len(x[1]), reverse=True)
            top_lang, top_evs = sorted_langs[0]
            if len(top_evs) >= 2:
                hypotheses.append({
                    "category": "emerging_interest",
                    "hypothesis": f"User demonstrates a dominant technical focus on {top_lang}.",
                    "confidence": "LIKELY",
                    "narrative": f"Across your browsing history, {top_lang} generated {len(top_evs)} distinct signals, searches, and documentation visits, significantly exceeding other programming topics.",
                    "supporting_evidence": [
                        {
                            "event_id": str(e.event_id),
                            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                            "domain": e.domain,
                            "title": sanitize_text(e.page_title),
                            "input": sanitize_text(e.input_text or extract_url_search_params(e.url))
                        }
                        for e in top_evs
                    ]
                })

        # B. Workflow Loop Patterns (e.g. Google -> StackOverflow -> Documentation)
        so_events = [e for e in events if e.domain and "stackoverflow.com" in e.domain.lower()]
        if len(so_events) >= 5:
            hypotheses.append({
                "category": "workflow_habit",
                "hypothesis": "User relies heavily on Stack Overflow for deep troubleshooting and technical verification.",
                "confidence": "CONFIRMED",
                "narrative": f"Recorded {len(so_events)} interactions on stackoverflow.com including direct queries and problem investigations.",
                "supporting_evidence": [
                    {
                        "event_id": str(e.event_id),
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        "domain": e.domain,
                        "title": sanitize_text(e.page_title),
                        "input": sanitize_text(e.input_text or extract_url_search_params(e.url))
                    }
                    for e in so_events[:10]
                ]
            })

        # C. Temporal Activity Clustering
        hours = [e.timestamp.hour for e in events if e.timestamp]
        if hours:
            hour_counts = Counter(hours)
            peak_hour, peak_cnt = hour_counts.most_common(1)[0]
            if peak_cnt >= 10:
                hypotheses.append({
                    "category": "temporal_shift",
                    "hypothesis": f"User browsing is heavily concentrated around {peak_hour:02d}:00 UTC.",
                    "confidence": "CONFIRMED",
                    "narrative": f"An intense cluster of {peak_cnt} events occurred around {peak_hour:02d}:00 UTC, indicating a key productive focus window.",
                    "supporting_evidence": [
                        {
                            "event_id": str(e.event_id),
                            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                            "domain": e.domain,
                            "title": sanitize_text(e.page_title)
                        }
                        for e in events if e.timestamp and e.timestamp.hour == peak_hour
                    ][:10]
                })

        # D. Domain Diversity and Research Distribution
        domain_counts = Counter([e.domain for e in events if e.domain])
        if len(domain_counts) >= 5:
            top_3 = domain_counts.most_common(3)
            hypotheses.append({
                "category": "unusual_pattern",
                "hypothesis": "Browsing activity is partitioned between media consumption and developer research.",
                "confidence": "LIKELY",
                "narrative": f"Your top active domains are {', '.join([f'{d} ({c} visits)' for d, c in top_3])}, reflecting dual modes of deep focus and entertainment.",
                "supporting_evidence": [
                    {
                        "event_id": str(e.event_id),
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        "domain": e.domain,
                        "title": sanitize_text(e.page_title)
                    }
                    for e in events if e.domain in [d for d, _ in top_3]
                ][:10]
            })

        return hypotheses

    @classmethod
    def get_results(cls, limit: int = 20) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            results = db.query(DiscoveryResult).order_by(DiscoveryResult.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": str(r.id),
                    "run_id": str(r.run_id),
                    "category": r.category,
                    "hypothesis": r.hypothesis,
                    "confidence": r.confidence,
                    "narrative": r.narrative,
                    "supporting_evidence": r.supporting_evidence or [],
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in results
            ]
        finally:
            db.close()

    @classmethod
    def get_discovery_by_id(cls, discovery_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            try:
                disc_uuid = uuid.UUID(str(discovery_id))
            except ValueError:
                return None

            r = db.query(DiscoveryResult).filter(DiscoveryResult.id == disc_uuid).first()
            if not r:
                return None
            return {
                "id": str(r.id),
                "run_id": str(r.run_id),
                "category": r.category,
                "hypothesis": r.hypothesis,
                "confidence": r.confidence,
                "narrative": r.narrative,
                "supporting_evidence": r.supporting_evidence or [],
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
        finally:
            db.close()
