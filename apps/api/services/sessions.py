from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from models.events import Event
from models.sessions import BrowserSession
from utils.sessionization import group_events_into_sessions, EventLike


class DummySessionEvent(EventLike):
    """
    A lightweight proxy to represent the end of the last known session
    so we can feed it into the pure sessionization algorithm.
    """

    def __init__(self, session_id: uuid.UUID, timestamp: datetime):
        self.session_id = session_id
        self.timestamp = timestamp
        self.is_dummy = True


def assign_unassigned_events_to_sessions(
    db: Session, threshold_minutes: int = 30
) -> dict:
    """
    Processes all events without a session_id chronologically and assigns them to
    existing or new sessions using the deterministic Task 3.2 algorithm.
    """
    # 1. Fetch unassigned events chronologically
    unassigned_events = (
        db.query(Event)
        .filter(Event.session_id == None)
        .order_by(Event.timestamp.asc())
        .all()
    )

    if not unassigned_events:
        return {"processed": 0, "sessions_created": 0, "sessions_updated": 0}

    # 2. Find the most recent session to see if we can append to it
    latest_session = (
        db.query(BrowserSession).order_by(BrowserSession.end_time.desc()).first()
    )

    events_to_group = []

    # Prepend a dummy event representing the end of the latest session
    if latest_session:
        dummy = DummySessionEvent(
            session_id=latest_session.id, timestamp=latest_session.end_time
        )
        events_to_group.append(dummy)

    events_to_group.extend(unassigned_events)

    # 3. Use the pure algorithm from Task 3.2
    session_groups = group_events_into_sessions(
        events_to_group, inactivity_threshold_minutes=threshold_minutes
    )

    sessions_created = 0
    sessions_updated = 0

    for group in session_groups:
        if not group:
            continue

        first_item = group[0]

        # Case A: This group merged with the latest existing session
        if getattr(first_item, "is_dummy", False):
            # The dummy is index 0. The rest are real unassigned events.
            real_events = group[1:]
            if not real_events:
                continue

            # latest_session is guaranteed to be populated here
            for ev in real_events:
                ev.session_id = latest_session.id

            latest_session.end_time = real_events[-1].timestamp
            latest_session.event_count += len(real_events)
            sessions_updated += 1

        # Case B: This group forms a brand new session
        else:
            # All items are real unassigned events
            start_time = group[0].timestamp
            end_time = group[-1].timestamp

            new_session = BrowserSession(
                start_time=start_time, end_time=end_time, event_count=len(group)
            )
            db.add(new_session)
            db.flush()  # Get the new_session.id

            for ev in group:
                ev.session_id = new_session.id

            sessions_created += 1

    db.commit()

    return {
        "processed": len(unassigned_events),
        "sessions_created": sessions_created,
        "sessions_updated": sessions_updated,
    }
