import pytest
from datetime import datetime, timedelta
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


from models.base import Base
from models.events import Event
from models.sessions import BrowserSession
from services.sessions import assign_unassigned_events_to_sessions

# Setup in-memory SQLite for isolated DB tests
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


event_id_counter = 1


def create_event(db, timestamp: datetime):
    global event_id_counter
    e = Event(
        id=event_id_counter,
        event_id=uuid.uuid4(),
        timestamp=timestamp,
        event_type="page_loaded",
        source="test",
        url="http://example.com",
    )
    event_id_counter += 1
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


def test_events_belonging_to_one_session(db):
    base = datetime(2023, 1, 1, 12, 0)
    e1 = create_event(db, base)
    e2 = create_event(db, base + timedelta(minutes=15))

    res = assign_unassigned_events_to_sessions(db)

    assert res["processed"] == 2
    assert res["sessions_created"] == 1
    assert res["sessions_updated"] == 0

    session = db.query(BrowserSession).first()
    assert session.event_count == 2
    assert session.start_time == e1.timestamp
    assert session.end_time == e2.timestamp

    db.refresh(e1)
    db.refresh(e2)
    assert e1.session_id == session.id
    assert e2.session_id == session.id


def test_events_separated_by_more_than_30_minutes(db):
    base = datetime(2023, 1, 1, 12, 0)
    e1 = create_event(db, base)
    e2 = create_event(db, base + timedelta(minutes=31))

    res = assign_unassigned_events_to_sessions(db)
    assert res["sessions_created"] == 2

    s1 = db.query(BrowserSession).filter(BrowserSession.start_time == base).first()
    s2 = (
        db.query(BrowserSession)
        .filter(BrowserSession.start_time == e2.timestamp)
        .first()
    )

    assert s1.event_count == 1
    assert s2.event_count == 1

    db.refresh(e1)
    db.refresh(e2)
    assert e1.session_id == s1.id
    assert e2.session_id == s2.id


def test_exactly_30_minutes_same_session(db):
    base = datetime(2023, 1, 1, 12, 0)
    create_event(db, base)
    create_event(db, base + timedelta(minutes=30))

    assign_unassigned_events_to_sessions(db)
    assert db.query(BrowserSession).count() == 1


def test_events_out_of_chronological_order(db):
    base = datetime(2023, 1, 1, 12, 0)
    # Insert e2 before e1
    e2 = create_event(db, base + timedelta(minutes=10))
    e1 = create_event(db, base)

    assign_unassigned_events_to_sessions(db)

    # Still creates one session securely due to chronological sorting in service
    session = db.query(BrowserSession).first()
    assert session.event_count == 2
    assert session.start_time == e1.timestamp
    assert session.end_time == e2.timestamp


def test_idempotency_and_repeated_processing(db):
    base = datetime(2023, 1, 1, 12, 0)
    create_event(db, base)

    res1 = assign_unassigned_events_to_sessions(db)
    assert res1["processed"] == 1
    assert res1["sessions_created"] == 1

    # Run again with no new events
    res2 = assign_unassigned_events_to_sessions(db)
    assert res2["processed"] == 0
    assert res2["sessions_created"] == 0
    assert db.query(BrowserSession).count() == 1

    # Add a new event that should append to the first session
    create_event(db, base + timedelta(minutes=15))
    res3 = assign_unassigned_events_to_sessions(db)
    assert res3["processed"] == 1
    assert res3["sessions_created"] == 0
    assert res3["sessions_updated"] == 1

    session = db.query(BrowserSession).first()
    assert session.event_count == 2


def test_configurable_threshold(db):
    base = datetime(2023, 1, 1, 12, 0)
    create_event(db, base)
    create_event(db, base + timedelta(minutes=20))

    # Using a 15-minute threshold will split them
    res = assign_unassigned_events_to_sessions(db, threshold_minutes=15)
    assert res["sessions_created"] == 2
