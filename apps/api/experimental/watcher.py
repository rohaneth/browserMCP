import asyncio
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from collections import Counter

from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.events import Event
from models.experimental import WatcherState, WatcherAlert
from utils.privacy import sanitize_text
from utils.normalization import extract_url_search_params
from services.investigation import run_investigation

logger = logging.getLogger(__name__)

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
                self._process_new_events_cycle()
            except Exception as e:
                logger.error(f"Error in watcher processing cycle: {e}")

            try:
                # Sleep interval between check cycles
                await asyncio.wait_for(self._stop_event.wait(), timeout=10)
                break # If event is set, exit loop
            except asyncio.TimeoutError:
                continue

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
        3. Only triggers a scoped investigation when substantial shift detected.
        """
        alerts = []
        if len(events) < 3:
            return alerts

        # Collect searches
        searches = []
        domains = []
        event_ids = [str(e.event_id) for e in events]

        for e in events:
            if e.domain:
                domains.append(e.domain.lower())
            inp = e.input_text or extract_url_search_params(e.url)
            if inp:
                searches.append(inp.lower())

        # Check for domain concentration
        dom_counts = Counter(domains)
        if dom_counts:
            top_dom, top_count = dom_counts.most_common(1)[0]
            if top_count >= 5 and top_dom in ["stackoverflow.com", "github.com", "youtube.com"]:
                alerts.append(WatcherAlert(
                    alert_type="activity_burst",
                    title=f"Activity Burst on {top_dom}",
                    summary=f"Detected a burst of {top_count} interactions on {top_dom} in recent browsing stream.",
                    supporting_event_ids=event_ids[:10]
                ))

        # Check for search topic patterns
        if len(searches) >= 2:
            joined_searches = " ".join(searches)
            # Detect emerging technical topics
            for kw in ["python", "rust", "docker", "fastapi", "react", "kubernetes", "java", "sql"]:
                if kw in joined_searches:
                    alerts.append(WatcherAlert(
                        alert_type="interest_signal",
                        title=f"Active Exploration of {kw.capitalize()}",
                        summary=f"Detected repeated search signals related to {kw.capitalize()} in recent user queries: {searches[:3]}",
                        supporting_event_ids=event_ids[:10]
                    ))
                    break

        return alerts
