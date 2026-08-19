from utils.normalization import normalize_url, normalize_domain
from schemas.events import BrowserEvent, EventType
from datetime import datetime
import uuid


def test_normalize_url_removes_tracking_but_preserves_legitimate():
    url = "https://WWW.Example.com:443/path?utm_source=x&q=test"
    result = normalize_url(url)
    assert result == "https://WWW.Example.com:443/path?q=test"


def test_normalize_url_with_fragment():
    url = "https://example.com/path?utm_source=twitter#section1"
    assert normalize_url(url) == "https://example.com/path#section1"


def test_normalize_url_multiple_tracking_parameters():
    url = "https://example.com/?fbclid=123&gclid=456&utm_campaign=summer&legit=1"
    assert normalize_url(url) == "https://example.com/?legit=1"


def test_normalize_url_query_only_legitimate():
    url = "https://example.com/search?q=hello&page=2"
    assert normalize_url(url) == "https://example.com/search?q=hello&page=2"


def test_normalize_url_malformed():
    # Should safely return the original without crashing
    assert normalize_url("not_a_valid_url") == "not_a_valid_url"
    assert normalize_url(None) is None


def test_normalize_url_deterministic():
    url = "https://example.com/?utm_source=x&q=1"
    first = normalize_url(url)
    second = normalize_url(first)
    assert first == "https://example.com/?q=1"
    assert first == second


def test_normalize_domain_stripping_and_lowercasing():
    assert normalize_domain("WWW.Example.com") == "example.com"
    assert normalize_domain("example.com:443") == "example.com"
    assert normalize_domain("WWW.Example.com:8080") == "example.com"


def test_normalize_domain_preserves_subdomains():
    assert normalize_domain("app.example.com") == "app.example.com"
    assert normalize_domain("www.app.example.com") == "app.example.com"


def test_normalize_domain_infers_from_url():
    # missing domain + valid URL -> inferred
    assert normalize_domain(None, "https://WWW.Example.com:443/path") == "example.com"
    # explicit domain + URL -> explicit domain takes precedence
    assert normalize_domain("explicit.com", "https://other.com/path") == "explicit.com"


def test_normalize_domain_safely_handles_missing():
    assert normalize_domain(None, None) is None
    assert normalize_domain(None, "not_a_url") is None


def test_browser_event_normalization_boundary():
    event = BrowserEvent(
        event_id=uuid.uuid4(),
        timestamp=datetime.now(),
        event_type=EventType.page_loaded,
        url="https://WWW.Example.com:443/path?utm_source=x&q=test",
        source="test",
    )
    # The Pydantic validator should have normalized both url and domain
    assert event.url == "https://WWW.Example.com:443/path?q=test"
    assert event.domain == "example.com"
