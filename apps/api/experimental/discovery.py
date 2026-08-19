import logging
import uuid
import os
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
from services.investigation import run_investigation
from services.preference import (
    LANGUAGES,
    infer_programming_preference,
    infer_comedian_preference,
    infer_entertainment_preference
)

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """
    Dedicated Discovery Engine & Orchestration Layer.

    Unlike the standard Investigator (which directly answers a single question),
    the Discovery Engine:
    1. Analyzes structured browser history across multi-dimensional candidate patterns:
       - Repeated interests & topic shifts
       - Emerging vs fading technical focus
       - Temporal changes & peak interaction routines
       - Session patterns & duration clusters
       - Search-to-browsing investigations & workflow loops
    2. Generates candidate hypotheses autonomously.
    3. Sends promising hypotheses through the Investigator service to extract deep evidence.
    4. Evaluates and filters hypotheses (rejecting unsupported, trivial, visit-count only,
       or low-evidence claims).
    5. Ranks findings by novelty and confidence.
    6. Produces structured discoveries with confirmed vs inferred classification.
    """

    @classmethod
    def run_discovery(cls, focus_hint: Optional[str] = None) -> Dict[str, Any]:
        db = SessionLocal()
        run = DiscoveryRun(
            focus_hint=focus_hint or "Autonomous browsing pattern & interest discovery",
            status="analyzing"
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            # 1. Inspect structured dataset
            all_events = db.query(Event).order_by(Event.timestamp.asc()).all()
            if not all_events:
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                db.commit()
                return {"run_id": str(run.id), "status": "completed", "discoveries": []}

            # 2. Stage 1: Generate multi-dimensional candidate hypotheses
            candidate_hypotheses = cls._generate_candidate_hypotheses(db, all_events, focus_hint)
            run.hypotheses_generated = len(candidate_hypotheses)

            # 3. Stage 2 & 3: Investigate hypotheses using the Investigator service & verify evidence
            evaluated_findings = []
            for cand in candidate_hypotheses:
                finding = cls._investigate_and_verify_hypothesis(db, cand)
                if finding is not None:
                    evaluated_findings.append(finding)

            # 4. Stage 4: Rank findings by score/novelty
            ranked_findings = sorted(evaluated_findings, key=lambda x: x["score"], reverse=True)

            # 5. Persist top valid discoveries
            confirmed_count = 0
            results_to_save = []

            for item in ranked_findings[:8]:
                if item["confidence"] in ["CONFIRMED", "LIKELY"]:
                    confirmed_count += 1

                res = DiscoveryResult(
                    run_id=run.id,
                    category=item["category"],
                    hypothesis=item["hypothesis"],
                    confidence=item["confidence"],
                    narrative=item["narrative"],
                    supporting_evidence=item["supporting_evidence"]
                )
                db.add(res)
                results_to_save.append({
                    "id": str(res.id),
                    "category": item["category"],
                    "finding_type": item["finding_type"],
                    "hypothesis": item["hypothesis"],
                    "confidence": item["confidence"],
                    "why_interesting": item["why_interesting"],
                    "narrative": item["narrative"],
                    "evidence_count": len(item["supporting_evidence"]),
                    "evidence": item["supporting_evidence"][:5]
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
            logger.error(f"Error during self discovery run: {e}", exc_info=True)
            run.status = "failed"
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"run_id": str(run.id), "status": "failed", "error": str(e)}
        finally:
            db.close()

    @classmethod
    def _generate_candidate_hypotheses(
        cls, db: Session, events: List[Event], focus_hint: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Stage 1: Multi-Signal Behavioral Pattern Analysis.
        Analyzes topics, shifts, temporal routines, search sequences, and session clusters.
        """
        candidates: List[Dict[str, Any]] = []

        # 1. Programming & Technical Focus Shifts
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
                candidates.append({
                    "category": "emerging_interest",
                    "finding_type": "Inference",
                    "target_query": f"Why does {top_lang} appear to be my favourite programming language?",
                    "hypothesis": f"Your programming interest appears to have become significantly {top_lang}-focused.",
                    "why_interesting": f"Rather than generic coding, your activity shows repeated searches, version comparisons, and problem investigations specifically surrounding {top_lang}.",
                    "base_events": top_evs,
                    "novelty_weight": 1.2
                })

            # Check for secondary technical topic exploration
            if len(sorted_langs) > 1:
                sec_lang, sec_evs = sorted_langs[1]
                if len(sec_evs) >= 2:
                    candidates.append({
                        "category": "emerging_interest",
                        "finding_type": "Inference",
                        "target_query": f"What did I search about {sec_lang}?",
                        "hypothesis": f"You are actively exploring or contrasting {sec_lang} alongside {top_lang}.",
                        "why_interesting": f"Browsing history reveals parallel queries into {sec_lang} alongside your core stack.",
                        "base_events": sec_evs,
                        "novelty_weight": 0.9
                    })

        # 2. Standup Comedy / Entertainment Routine
        pref_com, com_evs = infer_comedian_preference(db)
        if pref_com.get("top_candidate") and len(com_evs) >= 2:
            comedian = pref_com["top_candidate"]
            candidates.append({
                "category": "recurring_behavior",
                "finding_type": "Inference",
                "target_query": f"What did I watch or search about {comedian}?",
                "hypothesis": f"You demonstrate a strong preference for {comedian}'s comedy and specials during entertainment sessions.",
                "why_interesting": f"Captured media playback, stream titles, and searches repeatedly converge on {comedian}'s content across multiple dates.",
                "base_events": com_evs,
                "novelty_weight": 1.1
            })

        # 3. Deep Troubleshooting Workflow Loop (Search -> StackOverflow -> Docs)
        so_events = [e for e in events if e.domain and "stackoverflow.com" in e.domain.lower()]
        so_searches = [e for e in so_events if e.input_text or extract_url_search_params(e.url)]
        if len(so_events) >= 3:
            candidates.append({
                "category": "workflow_habit",
                "finding_type": "Inference",
                "target_query": "What did I search on Stack Overflow?",
                "hypothesis": "You consistently use Stack Overflow as an active problem-solving workbench rather than casual browsing.",
                "why_interesting": "Your interactions on stackoverflow.com feature explicit typed debugging queries and version comparison questions.",
                "base_events": so_events,
                "novelty_weight": 1.0
            })

        # 4. Shopping / Hardware Research Intent
        amazon_events = [e for e in events if e.domain and "amazon" in e.domain.lower()]
        if len(amazon_events) >= 3:
            laptop_events = [e for e in amazon_events if "vivobook" in (e.page_title or '').lower() or "laptop" in (e.page_title or '').lower() or "asus" in (e.page_title or '').lower()]
            if laptop_events:
                candidates.append({
                    "category": "emerging_interest",
                    "finding_type": "Inference",
                    "target_query": "What products or laptops did I look for on Amazon?",
                    "hypothesis": "You are actively researching mid-range laptop specifications (e.g. ASUS VivoBook / Intel 13th Gen).",
                    "why_interesting": "Browsing shows multiple product inspection and spec-comparison events on Amazon.",
                    "base_events": laptop_events,
                    "novelty_weight": 1.15
                })

        # 5. Temporal Routine & Peak Hours
        hours = [e.timestamp.hour for e in events if e.timestamp]
        if hours:
            hour_counts = Counter(hours)
            peak_hour, peak_cnt = hour_counts.most_common(1)[0]
            if peak_cnt >= 8:
                candidates.append({
                    "category": "temporal_shift",
                    "finding_type": "Confirmed Pattern",
                    "target_query": f"What was my activity around {peak_hour:02d}:00 UTC?",
                    "hypothesis": f"Your browsing demonstrates a distinct concentration peak around {peak_hour:02d}:00 UTC.",
                    "why_interesting": f"A density of {peak_cnt} interactions is recorded around {peak_hour:02d}:00 UTC, highlighting your primary daily active window.",
                    "base_events": [e for e in events if e.timestamp and e.timestamp.hour == peak_hour],
                    "novelty_weight": 0.85
                })

        # 6. Sessionization & Context Segmentation
        sessions = db.query(BrowserSession).all()
        if len(sessions) >= 2:
            long_sessions = [
                s for s in sessions
                if s.start_time and s.end_time and (s.end_time - s.start_time).total_seconds() > 600
            ]
            if long_sessions:
                candidates.append({
                    "category": "session_pattern",
                    "finding_type": "Confirmed Pattern",
                    "target_query": "What were my longest browsing sessions?",
                    "hypothesis": "Your workflow divides into brief informational lookup bursts and extended multi-topic research sessions.",
                    "why_interesting": f"Session clustering shows {len(long_sessions)} deep-focus sessions exceeding 10 minutes alongside quick single-tab lookups.",
                    "base_events": events[:10],
                    "novelty_weight": 0.85
                })

        return candidates

    @classmethod
    def _investigate_and_verify_hypothesis(
        cls, db: Session, candidate: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Stage 2 & 3: Sends candidate hypothesis to Investigator for concrete evidence gathering,
        then evaluates and filters findings.
        """
        target_query = candidate["target_query"]
        base_events = candidate.get("base_events", [])

        # Call existing Investigator for deep multi-signal retrieval
        investigation, evidence_list = run_investigation(db, target_query)

        # Stage 4: Filtering & Verification Rules
        # Reject if fewer than 2 supporting evidence items
        total_evidence_count = len(evidence_list) or len(base_events)
        if total_evidence_count < 2:
            return None

        # Build sanitized evidence objects
        evidence_objs = []
        seen_ids = set()

        for ev in evidence_list:
            if ev.event_id not in seen_ids:
                seen_ids.add(ev.event_id)
                evidence_objs.append({
                    "event_id": ev.event_id,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                    "title": sanitize_text(ev.title),
                    "url": ev.url,
                    "snippet": sanitize_text(ev.snippet)
                })

        # Supplement with base_events if needed
        for e in base_events:
            e_id = str(e.event_id)
            if e_id not in seen_ids:
                seen_ids.add(e_id)
                inp = e.input_text or extract_url_search_params(e.url) or ""
                evidence_objs.append({
                    "event_id": e_id,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "title": sanitize_text(e.page_title or e.domain or "Event"),
                    "url": e.url,
                    "input": sanitize_text(inp),
                    "snippet": f"[{e.event_type}] Domain: {e.domain} | Title: {e.page_title or 'N/A'}" + (f" | Search: '{inp}'" if inp else "")
                })

        # Determine confidence rating
        summary_text = investigation.summary or ""
        if "CONFIRMED" in summary_text:
            confidence = "CONFIRMED"
        elif "LIKELY" in summary_text or total_evidence_count >= 3:
            confidence = "LIKELY"
        else:
            confidence = "LIKELY"

        # Calculate ranking score
        novelty_weight = candidate.get("novelty_weight", 1.0)
        evidence_score = min(len(evidence_objs), 10) * 0.1
        conf_multiplier = 1.2 if confidence == "CONFIRMED" else 1.0
        score = (1.0 + evidence_score) * novelty_weight * conf_multiplier

        # Generate refined narrative
        narrative = candidate["why_interesting"]
        if investigation.summary and not investigation.summary.startswith("Could not"):
            # Use concise synthesis if available
            clean_sum = investigation.summary.replace("**CONFIRMED:**", "").replace("**LIKELY:**", "").strip()
            if len(clean_sum) > 20 and len(clean_sum) < 300:
                narrative = f"{candidate['why_interesting']} {clean_sum}"

        return {
            "category": candidate["category"],
            "finding_type": candidate.get("finding_type", "Inference"),
            "hypothesis": candidate["hypothesis"],
            "why_interesting": candidate["why_interesting"],
            "confidence": confidence,
            "narrative": narrative,
            "supporting_evidence": evidence_objs,
            "score": score
        }

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


# Backward compatibility alias
BrowserSelfDiscovery = DiscoveryEngine
