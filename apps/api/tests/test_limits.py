import pytest
from schemas.events import BrowserEvent, EventType, BatchEventRequest
from pydantic import ValidationError
from datetime import datetime
import uuid


def create_valid_event(**kwargs):
    default = {
        "event_id": uuid.uuid4(),
        "timestamp": datetime.now(),
        "event_type": EventType.page_loaded,
        "source": "test",
    }
    default.update(kwargs)
    return default


def test_content_near_maximum():
    # Valid content (100,000 characters limit)
    content = "a" * 100000
    event = BrowserEvent(**create_valid_event(content=content))
    assert len(event.content) == 100000


def test_content_exceeds_maximum():
    content = "a" * 100001
    with pytest.raises(ValidationError) as exc_info:
        BrowserEvent(**create_valid_event(content=content))
    assert "String should have at most 100000 characters" in str(exc_info.value)


def test_input_text_near_maximum():
    input_text = "a" * 10000
    event = BrowserEvent(**create_valid_event(input_text=input_text))
    assert len(event.input_text) == 10000


def test_input_text_exceeds_maximum():
    input_text = "a" * 10001
    with pytest.raises(ValidationError):
        BrowserEvent(**create_valid_event(input_text=input_text))


def test_oversized_url():
    url = "https://example.com/" + "a" * 2048
    with pytest.raises(ValidationError):
        BrowserEvent(**create_valid_event(url=url))


def test_oversized_page_title():
    title = "a" * 1001
    with pytest.raises(ValidationError):
        BrowserEvent(**create_valid_event(page_title=title))


def test_oversized_domain():
    domain = "a" * 256 + ".com"
    with pytest.raises(ValidationError):
        BrowserEvent(**create_valid_event(domain=domain))


def test_valid_metadata():
    metadata = {"key1": "value1", "key2": {"nested": "value2"}}
    event = BrowserEvent(**create_valid_event(metadata=metadata))
    assert event.metadata["key1"] == "value1"


def test_oversized_metadata_depth():
    # Exceeds max depth of 5
    metadata = {
        "level1": {"level2": {"level3": {"level4": {"level5": {"level6": "value"}}}}}
    }
    with pytest.raises(ValidationError) as exc_info:
        BrowserEvent(**create_valid_event(metadata=metadata))
    assert "nesting depth" in str(exc_info.value)


def test_oversized_metadata_keys():
    # Exceeds max keys of 100
    metadata = {f"key_{i}": i for i in range(101)}
    with pytest.raises(ValidationError) as exc_info:
        BrowserEvent(**create_valid_event(metadata=metadata))
    assert "maximum allowed keys" in str(exc_info.value)


def test_oversized_metadata_serialized_size():
    # Serialized size exceeds 10,000 bytes
    metadata = {"large_key": "a" * 10001}
    with pytest.raises(ValidationError) as exc_info:
        BrowserEvent(**create_valid_event(metadata=metadata))
    assert "serialized size" in str(exc_info.value)


def test_batch_within_limits():
    events = [BrowserEvent(**create_valid_event()) for _ in range(500)]
    batch = BatchEventRequest(events=events)
    assert len(batch.events) == 500


def test_batch_exceeds_limits():
    events = [BrowserEvent(**create_valid_event()) for _ in range(501)]
    with pytest.raises(ValidationError) as exc_info:
        BatchEventRequest(events=events)
    assert "List should have at most 500 items" in str(exc_info.value)
