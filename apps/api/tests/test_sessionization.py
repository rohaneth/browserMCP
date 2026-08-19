from datetime import datetime, timedelta
from utils.sessionization import group_events_into_sessions


class DummyEvent:
    def __init__(self, id: int, timestamp: datetime):
        self.id = id
        self.timestamp = timestamp


def test_empty_input():
    assert group_events_into_sessions([]) == []


def test_one_event():
    e1 = DummyEvent(1, datetime(2023, 1, 1, 12, 0))
    sessions = group_events_into_sessions([e1])
    assert len(sessions) == 1
    assert len(sessions[0]) == 1
    assert sessions[0][0].id == 1


def test_multiple_events_within_threshold():
    base = datetime(2023, 1, 1, 12, 0)
    e1 = DummyEvent(1, base)
    e2 = DummyEvent(2, base + timedelta(minutes=10))
    e3 = DummyEvent(3, base + timedelta(minutes=25))  # From e2, gap is 15

    sessions = group_events_into_sessions([e1, e2, e3])

    assert len(sessions) == 1
    assert len(sessions[0]) == 3


def test_gap_greater_than_threshold_new_session():
    base = datetime(2023, 1, 1, 12, 0)
    e1 = DummyEvent(1, base)
    e2 = DummyEvent(2, base + timedelta(minutes=31))  # Gap is 31 > 30

    sessions = group_events_into_sessions([e1, e2])

    assert len(sessions) == 2
    assert len(sessions[0]) == 1
    assert len(sessions[1]) == 1
    assert sessions[0][0].id == 1
    assert sessions[1][0].id == 2


def test_exactly_threshold_same_session():
    base = datetime(2023, 1, 1, 12, 0)
    e1 = DummyEvent(1, base)
    e2 = DummyEvent(2, base + timedelta(minutes=30))  # Exact threshold

    sessions = group_events_into_sessions([e1, e2])

    assert len(sessions) == 1
    assert len(sessions[0]) == 2


def test_configurable_threshold():
    base = datetime(2023, 1, 1, 12, 0)
    e1 = DummyEvent(1, base)
    e2 = DummyEvent(2, base + timedelta(minutes=15))

    # Under a 10 min threshold, these belong in different sessions
    sessions = group_events_into_sessions([e1, e2], inactivity_threshold_minutes=10)
    assert len(sessions) == 2


def test_events_supplied_out_of_chronological_order():
    base = datetime(2023, 1, 1, 12, 0)
    e1 = DummyEvent(1, base)
    e2 = DummyEvent(2, base + timedelta(minutes=10))
    e3 = DummyEvent(3, base + timedelta(minutes=50))

    # Shuffle input
    sessions = group_events_into_sessions([e3, e1, e2])

    # Expect deterministic chronological grouping: [e1, e2] then [e3]
    assert len(sessions) == 2
    assert sessions[0][0].id == 1
    assert sessions[0][1].id == 2
    assert sessions[1][0].id == 3


def test_deterministic_repeatable_results():
    base = datetime(2023, 1, 1, 12, 0)
    events = [
        DummyEvent(1, base),
        DummyEvent(2, base + timedelta(minutes=20)),
        DummyEvent(3, base + timedelta(minutes=51)),
        DummyEvent(4, base + timedelta(minutes=80)),
    ]

    s1 = group_events_into_sessions(events)
    s2 = group_events_into_sessions(events)
    s3 = group_events_into_sessions(reversed(events))

    # Verify same output length and contents
    assert len(s1) == 2  # [1, 2] and [3, 4]

    # Verify structure matches identically for all runs
    def extract_ids(session_groups):
        return [[e.id for e in session] for session in session_groups]

    assert extract_ids(s1) == [[1, 2], [3, 4]]
    assert extract_ids(s1) == extract_ids(s2)
    assert extract_ids(s1) == extract_ids(s3)
