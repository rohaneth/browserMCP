from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from schemas.events import BrowserEvent

class SearchQuery(BaseModel):
    keyword: str = Field(..., description="Search query string")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    domain: Optional[str] = None
    event_type: Optional[str] = None

class SearchResponse(BaseModel):
    events: List[BrowserEvent]
    total: int

class Evidence(BaseModel):
    event_id: str
    timestamp: datetime
    url: Optional[str]
    title: Optional[str]
    snippet: str
    relevance: float

class QueryRequest(BaseModel):
    question: str = Field(..., description="Question to answer based on events")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class QueryResponse(BaseModel):
    answer: str
    evidence: List[Evidence]
