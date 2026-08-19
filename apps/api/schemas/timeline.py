from typing import List
from pydantic import BaseModel, Field
from schemas.events import BrowserEvent


class TimelineResponse(BaseModel):
    events: List[BrowserEvent]
    total_count: int = Field(
        description="Total count of events matching the filter before pagination"
    )
    limit: int
    offset: int
