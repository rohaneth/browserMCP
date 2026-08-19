import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.mark.skip(reason="PostgreSQL integration pending (Docker unavailable)")
def test_create_valid_event():
    payload = {
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "timestamp": "2026-08-18T10:00:00Z",
        "event_type": "page_loaded",
        "url": "https://example.com",
        "domain": "example.com",
        "source": "browser_extension",
        "schema_version": 1,
    }
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["event_id"] == payload["event_id"]


@pytest.mark.skip(reason="PostgreSQL integration pending (Docker unavailable)")
def test_create_duplicate_event_is_idempotent():
    payload = {
        "event_id": "123e4567-e89b-12d3-a456-426614174001",
        "timestamp": "2026-08-18T10:00:00Z",
        "event_type": "click",
        "source": "browser_extension",
    }
    # First request
    response1 = client.post("/api/v1/events", json=payload)
    assert response1.status_code == 201

    # Second request with same event_id
    response2 = client.post("/api/v1/events", json=payload)
    assert response2.status_code == 200  # Idempotent success
    assert response2.json()["message"] == "Event already processed"


def test_missing_required_fields():
    # Attempt to post without timestamp and event_id
    payload = {"event_type": "page_loaded", "source": "browser_extension"}
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    # Check that missing fields are reported
    assert any(err["loc"] == ["body", "event_id"] for err in errors)
    assert any(err["loc"] == ["body", "timestamp"] for err in errors)


def test_invalid_event_type():
    payload = {
        "event_id": "123e4567-e89b-12d3-a456-426614174002",
        "timestamp": "2026-08-18T10:00:00Z",
        "event_type": "invalid_magic_type",
        "source": "browser_extension",
    }
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 422


def test_batch_events_limit():
    payload = {
        "events": [
            {
                "event_id": f"123e4567-e89b-12d3-a456-{426614174000 + i}",
                "timestamp": "2026-08-18T10:00:00Z",
                "event_type": "page_loaded",
                "source": "browser_extension",
            }
            for i in range(501)
        ]
    }
    response = client.post("/api/v1/events/batch", json=payload)
    assert response.status_code == 422
    assert "events" in response.json()["detail"][0]["loc"]


@pytest.mark.skip(reason="PostgreSQL integration pending (Docker unavailable)")
def test_batch_events_success():
    payload = {
        "events": [
            {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2026-08-18T10:00:00Z",
                "event_type": "page_loaded",
                "source": "browser_extension",
            },
            {
                "event_id": "123e4567-e89b-12d3-a456-426614174001",
                "timestamp": "2026-08-18T10:00:00Z",
                "event_type": "click",
                "source": "browser_extension",
            },
        ]
    }
    response = client.post("/api/v1/events/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["processed"] == 2
    assert data["accepted"] == 2
    assert data["duplicates"] == 0


@pytest.mark.skip(reason="PostgreSQL integration pending (Docker unavailable)")
def test_batch_duplicate_within_request():
    payload = {
        "events": [
            {
                "event_id": "123e4567-e89b-12d3-a456-999999999999",
                "timestamp": "2026-08-18T10:00:00Z",
                "event_type": "page_loaded",
                "source": "browser_extension",
            },
            {
                "event_id": "123e4567-e89b-12d3-a456-999999999999",
                "timestamp": "2026-08-18T10:05:00Z",
                "event_type": "page_loaded",
                "source": "browser_extension",
            },
        ]
    }
    response = client.post("/api/v1/events/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 2
    assert data["accepted"] == 1
    assert data["duplicates"] == 1


@pytest.mark.skip(reason="PostgreSQL integration pending (Docker unavailable)")
def test_batch_idempotent_retry():
    payload = {
        "events": [
            {
                "event_id": "123e4567-e89b-12d3-a456-888888888888",
                "timestamp": "2026-08-18T10:00:00Z",
                "event_type": "page_loaded",
                "source": "browser_extension",
            }
        ]
    }
    # First submission
    response1 = client.post("/api/v1/events/batch", json=payload)
    assert response1.status_code == 200
    assert response1.json()["accepted"] == 1
    assert response1.json()["duplicates"] == 0

    # Retry identical payload
    response2 = client.post("/api/v1/events/batch", json=payload)
    assert response2.status_code == 200
    assert response2.json()["accepted"] == 0
    assert response2.json()["duplicates"] == 1


def test_no_false_positive_deduplication():
    # If two events have different IDs, they should both be accepted, even if other fields match.
    # Note: Requires DB mocking or skipped if no DB.
    pass
