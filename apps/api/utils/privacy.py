import re
from typing import Any, Dict, Optional

# Pre-compiled high-confidence deterministic regex patterns
SENSITIVE_PATTERNS = [
    # Passwords and API Keys (e.g., password=secret, api_key: "secret")
    (
        re.compile(
            r'(?i)\b(password|passwd|api_key|apikey|api-key)(\s*[:=]\s*)([\'"]?)([^ \'"\r\n]+)\3'
        ),
        lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}[REDACTED]{m.group(3)}",
    ),
    # Bearer tokens (e.g., Authorization: Bearer abc123def...)
    (
        re.compile(r"(?i)\b(bearer\s+)([A-Za-z0-9\-._~+/]+=*)"),
        lambda m: f"{m.group(1)}[REDACTED]",
    ),
    # Private Keys (PEM format)
    (
        re.compile(
            r"(-----BEGIN [A-Z0-9 ]+ KEY-----)[\s\S]+?(-----END [A-Z0-9 ]+ KEY-----)"
        ),
        lambda m: f"{m.group(1)}\n[REDACTED]\n{m.group(2)}",
    ),
    # Credit Card numbers (basic heuristic: 13-16 digits with optional spaces/dashes)
    (re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"), lambda m: "[REDACTED_CC]"),
]


def sanitize_text(text: Optional[str]) -> Optional[str]:
    """
    Scans text for high-confidence sensitive data and redacts it.
    Returns the sanitized string.
    """
    if not text:
        return text

    sanitized = text
    for pattern, replacer in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacer, sanitized)

    return sanitized


def sanitize_metadata(metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Recursively scans strings inside metadata dictionaries and lists.
    """
    if not metadata:
        return metadata

    def traverse(obj: Any) -> Any:
        if isinstance(obj, str):
            return sanitize_text(obj)
        elif isinstance(obj, dict):
            return {k: traverse(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [traverse(item) for item in obj]
        return obj

    return traverse(metadata)


def sanitize_event(event: Any) -> Any:
    """
    Sanitizes all relevant textual fields of a BrowserEvent.
    Expects a Pydantic model instance and modifies it in-place.
    """
    if getattr(event, "content", None):
        event.content = sanitize_text(event.content)

    if getattr(event, "input_text", None):
        event.input_text = sanitize_text(event.input_text)

    if getattr(event, "page_title", None):
        event.page_title = sanitize_text(event.page_title)

    if getattr(event, "metadata", None):
        event.metadata = sanitize_metadata(event.metadata)

    return event
