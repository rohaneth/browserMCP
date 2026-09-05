import asyncio
import logging
import os
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import Counter
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.events import Event
from models.experimental import WatcherState, WatcherAlert
from utils.privacy import sanitize_text
from utils.normalization import extract_url_search_params
from services.investigation import run_investigation

logger = logging.getLogger(__name__)

EVENTS_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../events.log'))


class BrowserWatcher:
    _instance: Optional["BrowserWatcher"] = None

    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    @classmethod
    def get_instance(cls) -> "BrowserWatcher":
        if cls._instance is None:
            cls._instance = BrowserWatcher()
        return cls._instance

    def _get_or_create_state(self, db: Session) -> WatcherState:
        state = db.query(WatcherState).filter(WatcherState.id == 1).first()
        if not state:
            state = WatcherState(
                id=1,
                is_running=False,
                total_events_observed=0,
                total_alerts_triggered=0,
                active_focus="Continuous browser pattern & interest monitoring"
            )
            db.add(state)
            db.commit()
            db.refresh(state)
        return state

    async def start(self, focus: Optional[str] = None) -> Dict[str, Any]:
        """Starts the continuous browser watcher in the background."""
        if self.is_running:
            return {"status": "already_running", "message": "Watcher is already running."}

        self.is_running = True
        self._stop_event.clear()

        # Update persistent state
        db = SessionLocal()
        try:
            state = self._get_or_create_state(db)
            state.is_running = True
            if focus:
                state.active_focus = focus
            db.commit()
        finally:
            db.close()

        self._task = asyncio.create_task(self._run_loop())
        logger.info("Continuous Browser Watcher started.")
        return {"status": "started", "message": "Watcher service started successfully."}

    async def stop(self) -> Dict[str, Any]:
        """Stops the continuous browser watcher."""
        if not self.is_running:
            return {"status": "not_running", "message": "Watcher is not currently running."}

        self.is_running = False
        self._stop_event.set()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        db = SessionLocal()
        try:
            state = self._get_or_create_state(db)
            state.is_running = False
            db.commit()
        finally:
            db.close()

        logger.info("Continuous Browser Watcher stopped.")
        return {"status": "stopped", "message": "Watcher service stopped cleanly."}

    def get_status(self) -> Dict[str, Any]:
        """Returns the current state and statistics of the watcher."""
        db = SessionLocal()
        try:
            state = self._get_or_create_state(db)
            alerts_count = db.query(WatcherAlert).count()
            return {
                "is_running": self.is_running,
                "total_events_observed": state.total_events_observed,
                "total_alerts_triggered": alerts_count,
                "active_focus": state.active_focus,
                "last_processed_timestamp": state.last_processed_timestamp.isoformat() if state.last_processed_timestamp else None,
                "updated_at": state.updated_at.isoformat() if state.updated_at else None
            }
        finally:
            db.close()

    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent alert notifications produced by the watcher."""
        db = SessionLocal()
        try:
            alerts = db.query(WatcherAlert).order_by(WatcherAlert.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": str(a.id),
                    "alert_type": a.alert_type,
                    "title": a.title,
                    "summary": a.summary,
                    "supporting_event_ids": a.supporting_event_ids or [],
                    "created_at": a.created_at.isoformat() if a.created_at else None
                }
                for a in alerts
            ]
        finally:
            db.close()

    async def _run_loop(self):
        """Asynchronous background monitoring loop."""
        while self.is_running:
            try:
                # 1. Sync any new lines from events.log into DB if present
                self._sync_events_log_file()
                # 2. Process unprocessed events for heuristic shifts
                self._process_new_events_cycle()
            except Exception as e:
                logger.error(f"Error in watcher processing cycle: {e}", exc_info=True)

            try:
                # Sleep interval between check cycles
                await asyncio.wait_for(self._stop_event.wait(), timeout=5)
                break
            except asyncio.TimeoutError:
                continue

    def _sync_events_log_file(self):
        """
        Monitors events.log for newly appended lines and imports them into DB.
        """
        if not os.path.exists(EVENTS_LOG_PATH):
            return

        db = SessionLocal()
        try:
            with open(EVENTS_LOG_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                ts_str = data.get("timestamp")
                url = data.get("url", "")
                raw_event = data.get("event") or data.get("type") or "unknown"
                event_type_map = {
                    "input": "input_submitted",
                    "search": "search_submitted",
                    "form": "form_submitted",
                }
                event_type = event_type_map.get(raw_event, raw_event)
                page_title = data.get("pageTitle") or data.get("title") or ""
                input_text = data.get("input") or data.get("text") or ""
                content = data.get("content", "")

                if not ts_str:
                    continue

                try:
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except Exception:
                    continue

                domain = ""
                if url:
                    try:
                        domain = urlparse(url).netloc
                    except Exception:
                        pass

                if not input_text and url:
                    extr = extract_url_search_params(url)
                    if extr:
                        input_text = extr

                # Check if event already exists in DB
                existing = db.query(Event).filter(
                    Event.timestamp == dt,
                    Event.event_type == event_type,
                    Event.url == url
                ).first()

                if not existing:
                    new_ev = Event(
                        event_id=uuid.uuid4(),
                        timestamp=dt,
                        event_type=event_type,
                        url=url,
                        canonical_url=url,
                        domain=domain,
                        page_title=page_title,
                        content=content,
                        input_text=input_text,
                        metadata_={k: v for k, v in data.items() if k not in {"timestamp", "event", "type", "pageTitle", "title", "input", "text", "url", "content"}},
                        source="events_log_watcher",
                        schema_version=1
                    )
                    db.add(new_ev)

            db.commit()
        except Exception as e:
            logger.error(f"Error syncing events.log: {e}")
        finally:
            db.close()

    def _process_new_events_cycle(self):
        """Inspects newly arrived events and scans for interest signals without invoking heavy LLMs."""
        db = SessionLocal()
        try:
            state = self._get_or_create_state(db)

            # Query events for lightweight analysis
            query = db.query(Event)
            if state.last_processed_timestamp:
                query = query.filter(Event.timestamp > state.last_processed_timestamp)

            new_events = query.order_by(Event.timestamp.asc()).limit(100).all()
            
            # If no newer events, evaluate recent window (last 50 events) if alert table is empty
            if not new_events:
                existing_alerts_count = db.query(WatcherAlert).count()
                if existing_alerts_count == 0:
                    new_events = db.query(Event).order_by(Event.timestamp.desc()).limit(50).all()
                    if new_events:
                        new_events.reverse()
                else:
                    return

            # Multi-query phrase & pattern detection
            alerts = self._analyze_events_lightweight(db, new_events)

            for alert in alerts:
                db.add(alert)
                state.total_alerts_triggered += 1

            if new_events:
                state.last_processed_timestamp = new_events[-1].timestamp
                state.last_processed_event_id = new_events[-1].event_id
                state.total_events_observed += len(new_events)
            db.commit()

        finally:
            db.close()

    def _analyze_events_lightweight(self, db: Session, events: List[Event]) -> List[WatcherAlert]:
        """
        Lightweight multi-query rule evaluation:
        1. Extract exact words/phrases appearing in >= 2 distinct search queries.
        2. Ignore navigation terms (login, signup, close, etc.).
        3. Emit strictly factual interest signals with exact supporting query citations.
        """
        alerts = []
        if len(events) < 2:
            return alerts

        STOP_WORDS = {
            "the", "a", "an", "and", "or", "for", "of", "in", "on", "at", "to", "from",
            "is", "are", "was", "were", "vs", "not", "with", "without", "what", "how",
            "why", "can", "best", "when", "who", "does", "do", "you", "someone", "many",
            "sign", "up", "login", "close", "home", "back", "google", "search", "youtube",
            "under", "like", "which", "will", "exist", "more", "much", "need"
        }

        # Collect searches & event mapping
        searches_map = {}  # query_text -> list of event_ids
        domains = []
        titles = []

        for e in events:
            if e.domain:
                domains.append(e.domain.lower())
            if e.page_title:
                titles.append(e.page_title.lower())
            inp = e.input_text or extract_url_search_params(e.url)
            if inp and len(inp.strip()) > 3:
                q_clean = inp.strip().lower()
                # Ignore pure navigation queries
                if q_clean in {"sign up", "sign in", "login", "close", "home", "back"}:
                    continue
                if q_clean not in searches_map:
                    searches_map[q_clean] = []
                searches_map[q_clean].append(str(e.event_id))

        # Check for multi-query interest phrases (appearing in >= 2 distinct queries)
        queries = list(searches_map.keys())
        phrase_to_queries = {}

        for q in queries:
            words = re.findall(r'[a-zA-Z0-9]+', q)
            seen_in_q = set()
            # 1-grams
            for w in words:
                if len(w) > 2 and w not in STOP_WORDS:
                    seen_in_q.add(w)
            # 2-grams
            for i in range(len(words) - 1):
                w1, w2 = words[i], words[i+1]
                if w1 not in STOP_WORDS and w2 not in STOP_WORDS:
                    seen_in_q.add(f"{w1} {w2}")

            for phrase in seen_in_q:
                if phrase not in phrase_to_queries:
                    phrase_to_queries[phrase] = []
                phrase_to_queries[phrase].append(q)

        # Sort phrases by number of distinct supporting queries
        sorted_phrases = sorted(
            [(p, qs) for p, qs in phrase_to_queries.items() if len(qs) >= 2],
            key=lambda x: len(x[1]),
            reverse=True
        )

        emitted_topics = set()
        for phrase, sup_queries in sorted_phrases[:5]:
            topic_label = phrase.title()
            if topic_label in emitted_topics:
                continue

            # Gather event IDs from supporting queries
            sup_event_ids = []
            for sq in sup_queries:
                sup_event_ids.extend(searches_map.get(sq, []))

            # Deduplicate while preserving order
            unique_sup_queries = list(dict.fromkeys(sup_queries))
            unique_sup_events = list(dict.fromkeys(sup_event_ids))

            alerts.append(WatcherAlert(
                alert_type="interest_signal",
                title=f"Interest Signal: {topic_label}",
                summary=f"Detected repeated search signals related to '{topic_label}' across {len(unique_sup_queries)} queries: {unique_sup_queries[:3]}",
                supporting_event_ids=unique_sup_events[:10]
            ))
            emitted_topics.add(topic_label)

        # Domain burst detection
        dom_counts = Counter(domains)
        if dom_counts:
            top_dom, top_count = dom_counts.most_common(1)[0]
            if top_count >= 3 and top_dom in ["stackoverflow.com", "github.com", "youtube.com", "amazon.in", "amazon.com"]:
                alerts.append(WatcherAlert(
                    alert_type="activity_burst",
                    title=f"Activity Burst on {top_dom}",
                    summary=f"Detected a concentrated stream of {top_count} events on {top_dom}.",
                    supporting_event_ids=[str(e.event_id) for e in events[:10]]
                ))

        return alerts
