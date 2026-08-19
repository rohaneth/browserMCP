from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
import time
import uuid

from schemas.events import BrowserEvent, BatchEventRequest, BatchEventResponse
from db.session import get_db
from services.events import create_browser_event, create_browser_events_batch
from models.settings import CollectionSettings

logger = logging.getLogger(__name__)

router = APIRouter()


def _is_collection_paused(db: Session) -> bool:
    settings = db.query(CollectionSettings).filter(CollectionSettings.id == 1).first()
    return settings.is_paused if settings else False


@router.post(
    "/events", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any]
)
def create_event(event: BrowserEvent, db: Session = Depends(get_db)):
    """
    Ingest a new browser event.
    Returns 201 Created for new events.
    Returns 200 OK for duplicate events (Idempotent).
    """
    if _is_collection_paused(db):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": "paused",
                "event_id": str(event.event_id),
                "message": "Event collection is currently paused.",
            },
        )

    db_event, created = create_browser_event(db, event)

    response_data = {
        "status": "success",
        "event_id": str(db_event.event_id),
        "message": "Event recorded" if created else "Event already processed",
    }

    # If the event was a duplicate, return 200 instead of 201 to indicate idempotency.
    return JSONResponse(
        status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        content=response_data,
    )


@router.post(
    "/events/batch", status_code=status.HTTP_200_OK, response_model=BatchEventResponse
)
def create_events_batch_endpoint(
    request: BatchEventRequest, db: Session = Depends(get_db)
):
    """
    Ingest a batch of browser events.
    Efficiently ignores duplicates.
    """
    if _is_collection_paused(db):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": "paused",
                "processed": 0,
                "accepted": 0,
                "duplicates": 0,
                "message": "Event collection is currently paused.",
            },
        )

    start_time = time.time()
    request_id = str(uuid.uuid4())

    result = create_browser_events_batch(db, request.events)

    duration_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "Batch ingested",
        extra={
            "request_id": request_id,
            "received": result["processed"],
            "accepted": result["accepted"],
            "duplicates": result["duplicates"],
            "duration_ms": duration_ms,
        },
    )

    return BatchEventResponse(
        status="success",
        processed=result["processed"],
        accepted=result["accepted"],
        duplicates=result["duplicates"],
    )
