from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from schemas.events import BrowserEvent
from models.events import Event


def create_browser_event(db: Session, event_data: BrowserEvent) -> tuple[Event, bool]:
    """
    Persists a BrowserEvent to the database.
    Returns a tuple (event, created).
    'created' is True if it's a new insertion, False if it was a duplicate (idempotent success).
    """
    db_event = Event(
        event_id=event_data.event_id,
        timestamp=event_data.timestamp,
        event_type=event_data.event_type.value,
        url=event_data.url,
        canonical_url=event_data.url,
        domain=event_data.domain,
        page_title=event_data.page_title,
        content=event_data.content,
        input_text=event_data.input_text,
        metadata_=event_data.metadata,
        source=event_data.source,
        schema_version=event_data.schema_version,
    )

    try:
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event, True
    except IntegrityError as e:
        db.rollback()

        is_unique_violation = False

        # Prefer PostgreSQL structured error if available (psycopg2)
        if hasattr(e.orig, "pgcode") and e.orig.pgcode == "23505":
            # SQLSTATE 23505 is unique_violation. Ensure it's for event_id.
            error_str = str(e.orig).lower()
            if "ix_events_event_id" in error_str or "events_event_id" in error_str:
                is_unique_violation = True
        else:
            # Fallback for SQLite or other dialects during testing
            error_str = str(e.orig).lower()
            if "events.event_id" in error_str or "events_event_id" in error_str:
                is_unique_violation = True

        if is_unique_violation:
            existing_event = (
                db.query(Event).filter(Event.event_id == event_data.event_id).first()
            )
            if existing_event:
                return existing_event, False

        # Re-raise any other integrity error
        raise


def create_browser_events_batch(db: Session, events: list[BrowserEvent]) -> dict:
    """
    Persists a batch of BrowserEvents.
    Uses PostgreSQL ON CONFLICT DO NOTHING for efficient deduplication.
    """
    if not events:
        return {"processed": 0, "accepted": 0, "duplicates": 0}

    # Deduplicate within the payload based on event_id (keep last)
    unique_events = {}
    for ev in events:
        unique_events[ev.event_id] = ev

    from sqlalchemy.dialects.postgresql import insert as pg_insert

    values = [
        {
            "event_id": ev.event_id,
            "timestamp": ev.timestamp,
            "event_type": ev.event_type.value,
            "url": ev.url,
            "canonical_url": ev.url,
            "domain": ev.domain,
            "page_title": ev.page_title,
            "content": ev.content,
            "input_text": ev.input_text,
            "metadata_": ev.metadata,
            "source": ev.source,
            "schema_version": ev.schema_version,
        }
        for ev in unique_events.values()
    ]

    stmt = pg_insert(Event).values(values)
    stmt = stmt.on_conflict_do_nothing(index_elements=["event_id"])

    result = db.execute(stmt)
    db.commit()

    accepted = result.rowcount
    duplicates = len(events) - accepted

    return {"processed": len(events), "accepted": accepted, "duplicates": duplicates}
