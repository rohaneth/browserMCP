from utils.privacy import sanitize_text, sanitize_metadata
from schemas.events import BrowserEvent, EventType
from datetime import datetime
import uuid


def test_password_redaction():
    assert sanitize_text("password=mySecret123") == "password=[REDACTED]"
    assert sanitize_text("Passwd = 'mySecret123'") == "Passwd = '[REDACTED]'"
    assert sanitize_text('password:"mySecret123"') == 'password:"[REDACTED]"'
    assert sanitize_text("password: mySecret123") == "password: [REDACTED]"


def test_apikey_redaction():
    assert sanitize_text("api_key=AIzaSyB-12345") == "api_key=[REDACTED]"
    assert sanitize_text("API-KEY : AIzaSyB-12345") == "API-KEY : [REDACTED]"


def test_bearer_token_redaction():
    assert (
        sanitize_text("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR")
        == "Authorization: Bearer [REDACTED]"
    )
    assert sanitize_text("bearer  abc123def") == "bearer  [REDACTED]"


def test_private_key_redaction():
    key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\nxyz\n-----END RSA PRIVATE KEY-----"
    expected = (
        "-----BEGIN RSA PRIVATE KEY-----\n[REDACTED]\n-----END RSA PRIVATE KEY-----"
    )
    assert sanitize_text(key) == expected


def test_credit_card_redaction():
    assert (
        sanitize_text("My card is 1234-5678-9012-3456.") == "My card is [REDACTED_CC]."
    )
    assert sanitize_text("My card is 1234 5678 9012 3456") == "My card is [REDACTED_CC]"


def test_normal_text_unchanged():
    assert (
        sanitize_text("Hello world, this is a normal text.")
        == "Hello world, this is a normal text."
    )
    assert (
        sanitize_text("I lost my password yesterday") == "I lost my password yesterday"
    )  # No assignment


def test_normal_urls_unchanged():
    url = "https://example.com/login?redirect=dashboard"
    assert sanitize_text(url) == url


def test_normal_search_queries_unchanged():
    assert (
        sanitize_text("how to reset password in linux")
        == "how to reset password in linux"
    )


def test_multiple_secrets():
    text = "api_key=12345 and password=secret"
    assert sanitize_text(text) == "api_key=[REDACTED] and password=[REDACTED]"


def test_metadata_sanitization():
    meta = {
        "safe_key": "safe_value",
        "nested": {"token": "Bearer abc123def", "password": "password=secret"},
        "numbers": 42,
        "bool": True,
    }
    sanitized = sanitize_metadata(meta)
    assert sanitized["safe_key"] == "safe_value"
    assert sanitized["nested"]["token"] == "Bearer [REDACTED]"
    assert sanitized["nested"]["password"] == "password=[REDACTED]"
    assert sanitized["numbers"] == 42
    assert sanitized["bool"] is True


def test_event_semantics_preserved():
    event_id = uuid.uuid4()
    ts = datetime.now()
    event = BrowserEvent(
        event_id=event_id,
        timestamp=ts,
        event_type=EventType.page_loaded,
        url="https://example.com",
        source="test",
        content="password=secret123",
        metadata={"key": "Bearer abc123def"},
    )

    assert event.event_id == event_id
    assert event.timestamp == ts
    assert event.url == "https://example.com"
    assert event.content == "password=[REDACTED]"
    assert event.metadata["key"] == "Bearer [REDACTED]"


def test_deterministic_redaction():
    text = "password=secret"
    first = sanitize_text(text)
    second = sanitize_text(first)
    assert first == second == "password=[REDACTED]"
