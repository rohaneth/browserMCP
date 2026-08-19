from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, UUID4, model_validator, field_validator


class EventType(str, Enum):
    page_loaded = "page_loaded"
    page_content = "page_content"
    click = "click"
    link_clicked = "link_clicked"
    input_submitted = "input_submitted"
    search_submitted = "search_submitted"
    form_submitted = "form_submitted"
    conversation_started = "conversation_started"
    conversation_title_changed = "conversation_title_changed"
    attachment_added = "attachment_added"
    media_played = "media_played"
    media_paused = "media_paused"
    scroll = "scroll"
    navigation = "navigation"
    unknown = "unknown"


class BrowserEvent(BaseModel):
    event_id: UUID4
    timestamp: datetime
    event_type: EventType

    url: Optional[str] = Field(default=None, max_length=10000)
    domain: Optional[str] = Field(default=None, max_length=255)
    page_title: Optional[str] = Field(default=None, max_length=1000)

    content: Optional[str] = Field(default=None, max_length=100000)
    input_text: Optional[str] = Field(default=None, max_length=10000)

    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    session_id: Optional[UUID4] = Field(default=None)
    source: str = Field(..., max_length=100)
    schema_version: int = Field(default=1, ge=1)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not v:
            return v

        # Helper to check depth and count keys
        def check_depth_and_keys(obj, current_depth=0):
            if current_depth > 5:
                raise ValueError("Metadata exceeds maximum nesting depth of 5")

            key_count = 0
            if isinstance(obj, dict):
                key_count += len(obj)
                for value in obj.values():
                    key_count += check_depth_and_keys(value, current_depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    key_count += check_depth_and_keys(item, current_depth + 1)
            return key_count

        total_keys = check_depth_and_keys(v)
        if total_keys > 100:
            raise ValueError(
                f"Metadata exceeds maximum allowed keys (100), found {total_keys}"
            )

        import json

        try:
            serialized = json.dumps(v)
            if len(serialized) > 10000:
                raise ValueError("Metadata serialized size exceeds 10000 bytes")
        except TypeError:
            raise ValueError("Metadata is not JSON serializable")

        return v

    @model_validator(mode="after")
    def normalize_fields(self) -> "BrowserEvent":
        from utils.normalization import normalize_url, normalize_domain, extract_url_search_params

        self.url = normalize_url(self.url)
        self.domain = normalize_domain(self.domain, self.url)
        
        if not self.input_text and self.url:
            extracted_search = extract_url_search_params(self.url)
            if extracted_search:
                self.input_text = extracted_search

        return self

    @model_validator(mode="after")
    def sanitize_privacy_fields(self) -> "BrowserEvent":
        from utils.privacy import sanitize_event

        return sanitize_event(self)


class BatchEventRequest(BaseModel):
    events: list[BrowserEvent] = Field(
        ..., max_length=500, description="Batch of browser events (max 500)"
    )


class BatchEventResponse(BaseModel):
    status: str
    processed: int
    accepted: int
    duplicates: int
