import pytest
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import ValidationError

from schemas.events import BrowserEvent, EventType


def test_valid_page_loaded_event():
    event = BrowserEvent(
        event_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        event_type=EventType.page_loaded,
        url="https://example.com",
        domain="example.com",
        page_title="Example Domain",
        source="browser_extension",
    )
    assert event.event_type == "page_loaded"
    assert event.schema_version == 1


def test_valid_search_submitted_event():
    event = BrowserEvent(
        event_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        event_type=EventType.search_submitted,
        url="https://google.com/search?q=test",
        domain="google.com",
        input_text="test query",
        source="browser_extension",
    )
    assert event.event_type == "search_submitted"
    assert event.input_text == "test query"


def test_valid_click_event():
    event = BrowserEvent(
        event_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        event_type=EventType.click,
        url="https://example.com",
        domain="example.com",
        metadata={"x": 100, "y": 200, "tag": "button"},
        source="browser_extension",
    )
    assert event.metadata["tag"] == "button"


def test_missing_required_fields():
    with pytest.raises(ValidationError) as exc:
        BrowserEvent(event_type=EventType.page_loaded)
    errors = str(exc.value)
    assert "event_id" in errors
    assert "timestamp" in errors
    assert "source" in errors


def test_invalid_event_type():
    with pytest.raises(ValidationError):
        BrowserEvent(
            event_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            event_type="invalid_type",
            source="browser_extension",
        )


def test_invalid_timestamp():
    with pytest.raises(ValidationError):
        BrowserEvent(
            event_id=uuid4(),
            timestamp="not_a_time",
            event_type=EventType.click,
            source="browser_extension",
        )


def test_invalid_event_id():
    with pytest.raises(ValidationError):
        BrowserEvent(
            event_id="not_a_uuid",
            timestamp=datetime.now(timezone.utc),
            event_type=EventType.click,
            source="browser_extension",
        )


def test_oversized_content():
    oversized = "a" * 50001
    with pytest.raises(ValidationError):
        BrowserEvent(
            event_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            event_type=EventType.page_content,
            content=oversized,
            source="browser_extension",
        )


def test_invalid_metadata():
    with pytest.raises(ValidationError):
        BrowserEvent(
            event_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            event_type=EventType.click,
            metadata="not_a_dict",
            source="browser_extension",
        )


def test_schema_version_handling():
    event = BrowserEvent(
        event_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        event_type=EventType.page_loaded,
        source="browser_extension",
        schema_version=2,
    )
    assert event.schema_version == 2

    with pytest.raises(ValidationError):
        BrowserEvent(
            event_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            event_type=EventType.page_loaded,
            source="browser_extension",
            schema_version=0,
        )


def test_optional_fields():
    event = BrowserEvent(
        event_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        event_type=EventType.page_loaded,
        source="browser_extension",
    )
    assert event.url is None
    assert event.domain is None
    assert event.metadata == {}


def test_serialization_deserialization():
    original = BrowserEvent(
        event_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        event_type=EventType.search_submitted,
        input_text="test",
        source="browser_extension",
    )
    json_data = original.model_dump_json()
    assert isinstance(json_data, str)

    reconstructed = BrowserEvent.model_validate_json(json_data)
    assert reconstructed.event_id == original.event_id
    assert reconstructed.event_type == original.event_type
    assert reconstructed.input_text == original.input_text
