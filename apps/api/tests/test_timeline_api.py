import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import uuid

from main import app
from db.session import get_db
from models.base import Base
from models.events import Event
from models.sessions import BrowserSession

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup in-memory SQLite for isolated DB tests
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Patch sqlite for JSONB mapping
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

event_id_counter = 1


def create_test_event(
    db,
    timestamp: datetime,
    domain: str = "example.com",
    event_type: str = "page_loaded",
):
    global event_id_counter
    e = Event(
        id=event_id_counter,
        event_id=uuid.uuid4(),
        timestamp=timestamp,
        event_type=event_type,
        source="test",
        url=f"http://{domain}/path",
        domain=domain,
        schema_version=1,
    )
    event_id_counter += 1
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture(autouse=True)
def cleanup_db():
    # Clean up events table between tests
    db = TestingSessionLocal()
    db.query(Event).delete()
    db.commit()
    db.close()


def test_timeline_empty():
    res = client.get("/api/v1/timeline")
    assert res.status_code == 200
    data = res.json()
    assert data["events"] == []
    assert data["total_count"] == 0


def test_timeline_chronological_descending_order():
    db = TestingSessionLocal()
    base = datetime(2023, 1, 1, 12, 0)
    create_test_event(db, base)
    create_test_event(db, base + timedelta(minutes=1))
    create_test_event(db, base + timedelta(minutes=2))
    db.close()

    res = client.get("/api/v1/timeline")
    assert res.status_code == 200
    events = res.json()["events"]
    assert len(events) == 3

    # Newest first
    t0 = datetime.fromisoformat(events[0]["timestamp"]).replace(tzinfo=None)
    t1 = datetime.fromisoformat(events[1]["timestamp"]).replace(tzinfo=None)
    t2 = datetime.fromisoformat(events[2]["timestamp"]).replace(tzinfo=None)

    assert t0 > t1
    assert t1 > t2


def test_timeline_start_and_end_time_filters():
    db = TestingSessionLocal()
    base = datetime(2023, 1, 1, 12, 0)
    create_test_event(db, base - timedelta(minutes=10))  # outside
    create_test_event(db, base)  # inside
    create_test_event(db, base + timedelta(minutes=10))  # inside
    create_test_event(db, base + timedelta(minutes=20))  # outside
    db.close()

    start = base.isoformat()
    end = (base + timedelta(minutes=10)).isoformat()

    res = client.get(f"/api/v1/timeline?start_time={start}&end_time={end}")
    assert res.status_code == 200
    events = res.json()["events"]
    assert len(events) == 2
    assert res.json()["total_count"] == 2


def test_timeline_invalid_time_range():
    base = datetime(2023, 1, 1, 12, 0)
    start = (base + timedelta(minutes=10)).isoformat()
    end = base.isoformat()

    res = client.get(f"/api/v1/timeline?start_time={start}&end_time={end}")
    assert res.status_code == 400
    assert res.json()["detail"] == "start_time cannot be after end_time"


def test_timeline_domain_and_event_type_filters():
    db = TestingSessionLocal()
    base = datetime(2023, 1, 1, 12, 0)
    create_test_event(db, base, domain="example.com", event_type="page_loaded")
    create_test_event(db, base, domain="example.com", event_type="click")
    create_test_event(db, base, domain="other.com", event_type="page_loaded")
    db.close()

    # Filter domain only
    res1 = client.get("/api/v1/timeline?domain=example.com")
    assert len(res1.json()["events"]) == 2

    # Filter event_type only
    res2 = client.get("/api/v1/timeline?event_type=page_loaded")
    assert len(res2.json()["events"]) == 2

    # Filter both
    res3 = client.get("/api/v1/timeline?domain=example.com&event_type=click")
    assert len(res3.json()["events"]) == 1
    assert res3.json()["events"][0]["event_type"] == "click"


def test_timeline_pagination():
    db = TestingSessionLocal()
    base = datetime(2023, 1, 1, 12, 0)
    for i in range(5):
        create_test_event(db, base + timedelta(minutes=i))
    db.close()

    res1 = client.get("/api/v1/timeline?limit=2&offset=0")
    assert len(res1.json()["events"]) == 2
    assert res1.json()["total_count"] == 5

    res2 = client.get("/api/v1/timeline?limit=2&offset=2")
    assert len(res2.json()["events"]) == 2

    res3 = client.get("/api/v1/timeline?limit=2&offset=4")
    assert len(res3.json()["events"]) == 1
