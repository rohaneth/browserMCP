from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import UUID4
import logging

from db.session import get_db
from models.settings import CollectionSettings
from models.events import Event
from schemas.privacy import (
    PauseStatusResponse,
    DeleteEventResponse,
    DeleteDateRangeResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_or_create_settings(db: Session) -> CollectionSettings:
    settings = db.query(CollectionSettings).filter(CollectionSettings.id == 1).first()
    if not settings:
        settings = CollectionSettings(id=1, is_paused=False)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.post(
    "/pause", status_code=status.HTTP_200_OK, response_model=PauseStatusResponse
)
def pause_collection(db: Session = Depends(get_db)):
    """
    Pause browser event collection.
    New events will be rejected or ignored.
    """
    settings = _get_or_create_settings(db)
    settings.is_paused = True
    db.commit()
    logger.info("Collection paused by user request.")
    return PauseStatusResponse(
        status="success", is_paused=True, message="Event collection is now paused."
    )


@router.post(
    "/resume", status_code=status.HTTP_200_OK, response_model=PauseStatusResponse
)
def resume_collection(db: Session = Depends(get_db)):
    """
    Resume browser event collection.
    """
    settings = _get_or_create_settings(db)
    settings.is_paused = False
    db.commit()
    logger.info("Collection resumed by user request.")
    return PauseStatusResponse(
        status="success", is_paused=False, message="Event collection is now resumed."
    )


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=DeleteEventResponse,
)
def delete_event(event_id: UUID4, db: Session = Depends(get_db)):
    """
    Delete a specific browser event by its UUID.
    Idempotent: returns success even if event is already deleted.
    """
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        # Idempotent response
        return DeleteEventResponse(
            status="success", message="Event not found or already deleted."
        )

    db.delete(event)
    db.commit()

    # Note: MemoryEvidence rows are deleted automatically due to Postgres CASCADE on foreign key
    logger.info(f"Event {event_id} deleted by user request.")
    return DeleteEventResponse(status="success", message="Event deleted successfully.")


@router.delete(
    "/events", status_code=status.HTTP_200_OK, response_model=DeleteDateRangeResponse
)
def delete_events_range(
    start_time: datetime = Query(..., description="Start of the range (inclusive)"),
    end_time: datetime = Query(..., description="End of the range (exclusive)"),
    db: Session = Depends(get_db),
):
    """
    Delete events within a specified date/time range [start_time, end_time).
    """
    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time must be strictly before end_time",
        )

    query = db.query(Event).filter(
        Event.timestamp >= start_time, Event.timestamp < end_time
    )

    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    logger.info(f"Deleted {deleted_count} events in range [{start_time}, {end_time})")

    return DeleteDateRangeResponse(
        status="success",
        deleted_count=deleted_count,
        message=f"Successfully deleted {deleted_count} events.",
    )
