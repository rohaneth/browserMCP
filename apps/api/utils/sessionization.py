from typing import List, Iterable
from datetime import timedelta


# We duck-type the event object so it works with SQLAlchemy models or Pydantic schemas.
# It just needs to have a 'timestamp' attribute.
class EventLike:
    timestamp: any


def group_events_into_sessions(
    events: Iterable[EventLike], inactivity_threshold_minutes: int = 30
) -> List[List[EventLike]]:
    """
    Groups a list of events into sessions based on a deterministic time-gap algorithm.
    Events within 'inactivity_threshold_minutes' of the preceding event are grouped together.

    Args:
        events: An iterable of objects possessing a datetime 'timestamp' attribute.
        inactivity_threshold_minutes: The maximum gap in minutes between events in the same session.

    Returns:
        A list of sessions, where each session is a list of events.
    """
    if not events:
        return []

    # Ensure deterministic chronological order
    sorted_events = sorted(events, key=lambda x: x.timestamp)

    threshold = timedelta(minutes=inactivity_threshold_minutes)

    sessions = []
    current_session = [sorted_events[0]]

    for event in sorted_events[1:]:
        last_event = current_session[-1]

        # If the gap is within the threshold, it belongs to the current session
        if (event.timestamp - last_event.timestamp) <= threshold:
            current_session.append(event)
        else:
            # Otherwise, start a new session
            sessions.append(current_session)
            current_session = [event]

    # Add the last session
    if current_session:
        sessions.append(current_session)

    return sessions
