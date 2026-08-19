import os
import json
import uuid
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

from db.session import SessionLocal
from models.events import Event
from utils.normalization import extract_url_search_params

logger = logging.getLogger(__name__)

# Search candidate locations for events.log
def get_events_log_path() -> Optional[str]:
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../events.log')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../events.log')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../events.log')),
        os.path.abspath('events.log'),
        os.path.abspath('../events.log'),
        os.path.abspath('../../events.log'),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

_last_file_mtime: Optional[float] = None
_last_file_size: Optional[int] = None


def sync_events_log_to_db(force: bool = False) -> int:
    """
    Checks if events.log was modified since the last check and synchronizes
    any new or updated events into the database. Returns the count of newly added events.
    """
    global _last_file_mtime, _last_file_size

    log_path = get_events_log_path()
    if not log_path or not os.path.exists(log_path):
        return 0

    try:
        stat = os.stat(log_path)
        mtime = stat.st_mtime
        size = stat.st_size
    except Exception as e:
        logger.warning(f"Unable to stat events.log at {log_path}: {e}")
        return 0

    # Skip if file has not changed and not forced
    if not force and _last_file_mtime == mtime and _last_file_size == size:
        return 0

    _last_file_mtime = mtime
    _last_file_size = size

    db = SessionLocal()
    added_count = 0
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
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
            input_text = data.get("input") or data.get("text") or data.get("query") or ""
            content = data.get("content", "")

            if not ts_str:
                continue

            try:
                # Handle ISO format and Zulu UTC suffix
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
                    metadata_={
                        k: v for k, v in data.items()
                        if k not in {"timestamp", "event", "type", "pageTitle", "title", "input", "text", "query", "url", "content"}
                    },
                    source="events_log_auto_sync",
                    schema_version=1
                )
                db.add(new_ev)
                added_count += 1

        if added_count > 0:
            db.commit()
            logger.info(f"Auto-synchronized {added_count} new events from {log_path} into DB.")
    except Exception as e:
        logger.error(f"Error during events.log auto-synchronization: {e}", exc_info=True)
    finally:
        db.close()

    return added_count
