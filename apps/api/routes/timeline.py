from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional

from db.session import get_db
from models.events import Event
from schemas.timeline import TimelineResponse
from schemas.events import BrowserEvent

router = APIRouter(prefix="/api/v1/timeline", tags=["Timeline"])


@router.get("", response_model=TimelineResponse)
def get_timeline(
    start_time: Optional[datetime] = Query(
        None, description="Filter events after this time (inclusive)"
    ),
    end_time: Optional[datetime] = Query(
        None, description="Filter events before this time (inclusive)"
    ),
    domain: Optional[str] = Query(None, description="Filter by normalized domain"),
    event_type: Optional[str] = Query(None, description="Filter by event_type"),
    limit: int = Query(50, ge=1, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    query = db.query(Event)

    if start_time:
        query = query.filter(Event.timestamp >= start_time)
    if end_time:
        query = query.filter(Event.timestamp <= end_time)

    if start_time and end_time and start_time > end_time:
        raise HTTPException(
            status_code=400, detail="start_time cannot be after end_time"
        )

    if domain:
        # Since domain normalization lowers it, we ensure query uses lower
        query = query.filter(Event.domain == domain.lower())
    if event_type:
        query = query.filter(Event.event_type == event_type)

    # Deterministic chronological ordering (newest first for timeline)
    # Falling back to id to ensure absolute determinism for identical timestamps
    query = query.order_by(desc(Event.timestamp), desc(Event.id))

    total_count = query.count()
    events_db = query.offset(offset).limit(limit).all()

    # We must convert SQLAlchemy Event models to Pydantic BrowserEvent schemas.
    # The Pydantic model does post-validation, but since it's already in DB,
    # we can construct it via model_validate.
    response_events = []
    for e in events_db:
        response_events.append(
            BrowserEvent(
                event_id=e.event_id,
                timestamp=e.timestamp,
                event_type=e.event_type,
                url=e.url,
                domain=e.domain,
                page_title=e.page_title,
                content=e.content,
                input_text=e.input_text,
                metadata=e.metadata_,  # Column is metadata_
                session_id=e.session_id,
                source=e.source,
                schema_version=e.schema_version,
            )
        )

    return TimelineResponse(
        events=response_events, total_count=total_count, limit=limit, offset=offset
    )
