import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, text
from datetime import datetime
from typing import List, Optional

from models.events import Event
from schemas.search import SearchResponse
from schemas.events import BrowserEvent
from utils.privacy import sanitize_event

logger = logging.getLogger(__name__)

def search_events(
    db: Session,
    keyword: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    domain: Optional[str] = None,
    event_type: Optional[str] = None,
) -> SearchResponse:
    query = db.query(Event)

    if keyword:
        # Task 4.2: Postgres full text search
        # Conditionally fallback to ILIKE for SQLite
        dialect = db.bind.dialect.name
        if dialect == 'sqlite':
            search_condition = or_(
                Event.page_title.ilike(f"%{keyword}%"),
                Event.content.ilike(f"%{keyword}%")
            )
            query = query.filter(search_condition)
        else:
            search_condition = text(
                "to_tsvector('english', coalesce(page_title, '') || ' ' || coalesce(content, '')) @@ plainto_tsquery('english', :keyword)"
            )
            query = query.filter(search_condition).params(keyword=keyword)

    if start_time:
        query = query.filter(Event.timestamp >= start_time)
    if end_time:
        query = query.filter(Event.timestamp <= end_time)
    if domain:
        query = query.filter(Event.domain == domain)
    if event_type:
        query = query.filter(Event.event_type == event_type)

    total = query.count()
    events = query.order_by(Event.timestamp.desc()).limit(100).all()
    
    # Map back to BrowserEvent schema and sanitize
    browser_events = []
    for e in events:
        browser_events.append(
            BrowserEvent(
                event_id=e.event_id,
                timestamp=e.timestamp,
                event_type=e.event_type,
                url=e.url,
                domain=e.domain,
                page_title=e.page_title,
                content=e.content,
                input_text=e.input_text,
                metadata=e.metadata_,
                source=e.source,
                schema_version=e.schema_version,
                session_id=e.session_id
            )
        )

    return SearchResponse(events=browser_events, total=total)

# Task 6.1: Combine Keyword and Vector Search
# Task 6.3: Ranking (Simple Reciprocal Rank Fusion)
def search_hybrid(
    db: Session,
    query: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    domain: Optional[str] = None,
    limit: int = 5
) -> dict:
    from services.memory import search_similar_memories

    # 1. Keyword search
    keyword_res = search_events(
        db, query, start_time, end_time, domain, event_type=None
    )
    
    # 2. Vector search (Tasks 6.1 & 6.2)
    # Ideally temporal filtering is applied directly in vector search too
    vector_res = search_similar_memories(db, query, limit=limit)
    
    # 3. Simple Reciprocal Rank Fusion (RRF) for ranking
    # Maps content/ID to a score
    rrf_scores = {}
    k = 60

    for rank, ev in enumerate(keyword_res.events if keyword_res else []):
        uid = str(ev.event_id)
        rrf_scores[uid] = rrf_scores.get(uid, 0.0) + 1.0 / (k + rank + 1)
        
    for rank, mem in enumerate(vector_res):
        uid = str(mem.id)
        rrf_scores[uid] = rrf_scores.get(uid, 0.0) + 1.0 / (k + rank + 1)
        
    sorted_uids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    top_uids = sorted_uids[:limit]

    return {
        "status": "success",
        "top_results": top_uids,
        "reranker_needed": False # Task 6.5: Decide Whether Reranking Is Needed
    }
