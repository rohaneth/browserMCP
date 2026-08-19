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
                event_type = data.get("event") or data.get("type") or "unknown"
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
        """Inspects newly arrived events without invoking LLMs on every single event."""
        db = SessionLocal()
        try:
            state = self._get_or_create_state(db)

            # Query events newer than last processed timestamp
            query = db.query(Event)
            if state.last_processed_timestamp:
                query = query.filter(Event.timestamp > state.last_processed_timestamp)

            new_events = query.order_by(Event.timestamp.asc()).limit(100).all()
            if not new_events:
                return

            # Lightweight pattern detection
            alerts = self._analyze_events_lightweight(db, new_events)

            for alert in alerts:
                db.add(alert)
                state.total_alerts_triggered += 1

            state.last_processed_timestamp = new_events[-1].timestamp
            state.last_processed_event_id = new_events[-1].event_id
            state.total_events_observed += len(new_events)
            db.commit()

        finally:
            db.close()

    def _analyze_events_lightweight(self, db: Session, events: List[Event]) -> List[WatcherAlert]:
        """
        Lightweight heuristic rule evaluation:
        1. High concentration / burst of queries on a specific new technical topic or language.
        2. Domain cluster switch (e.g. pivoting into research or entertainment).
        3. Media consumption or shopping shift detection.
        """
        alerts = []
        if len(events) < 2:
            return alerts

        # Collect searches & domains
        searches = []
        domains = []
        titles = []
        event_ids = [str(e.event_id) for e in events]

        for e in events:
            if e.domain:
                domains.append(e.domain.lower())
            if e.page_title:
                titles.append(e.page_title.lower())
            inp = e.input_text or extract_url_search_params(e.url)
            if inp:
                searches.append(inp.lower())

        # Check for domain concentration
        dom_counts = Counter(domains)
        if dom_counts:
            top_dom, top_count = dom_counts.most_common(1)[0]
            if top_count >= 3 and top_dom in ["stackoverflow.com", "github.com", "youtube.com", "amazon.in", "amazon.com"]:
                alerts.append(WatcherAlert(
                    alert_type="activity_burst",
                    title=f"Activity Burst on {top_dom}",
                    summary=f"Detected a concentrated stream of {top_count} events on {top_dom}.",
                    supporting_event_ids=event_ids[:10]
                ))

        # Check for search topic patterns
        if searches:
            joined_searches = " ".join(searches)
            for kw in ["python", "rust", "docker", "fastapi", "react", "kubernetes", "java", "sql", "vivobook", "laptop"]:
                if kw in joined_searches:
                    alerts.append(WatcherAlert(
                        alert_type="interest_signal",
                        title=f"Active Exploration of {kw.capitalize()}",
                        summary=f"Detected repeated search signals related to {kw.capitalize()} in recent user queries: {searches[:3]}",
                        supporting_event_ids=event_ids[:10]
                    ))
                    break

        # Check for entertainment stream (e.g. YouTube Standup or Video sessions)
        joined_titles = " ".join(titles)
        if "samay raina" in joined_titles or "standup" in joined_titles or "special" in joined_titles:
            alerts.append(WatcherAlert(
                alert_type="entertainment_session",
                title="Entertainment & Media Playback Detected",
                summary="Detected active video consumption and entertainment streaming session.",
                supporting_event_ids=event_ids[:10]
            ))

        return alerts
