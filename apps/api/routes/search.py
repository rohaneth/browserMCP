from fastapi import APIRouter, Depends, status, HTTPException
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from db.session import get_db
from schemas.search import SearchResponse, SearchQuery, QueryRequest, QueryResponse, Evidence
from services.search import search_events

router = APIRouter()

@router.get("/events/search", response_model=SearchResponse)
def get_events_search(
    keyword: str,
    start_time: datetime = None,
    end_time: datetime = None,
    domain: str = None,
    event_type: str = None,
    db: Session = Depends(get_db)
):
    """
    Search browser events using keyword and filters.
    """
    return search_events(db, keyword, start_time, end_time, domain, event_type)

@router.post("/query", response_model=QueryResponse)
def get_query_answer(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Advanced Question Answering endpoint using Agentic Investigation (Phase 8).
    """
    from services.investigation import run_investigation
    
    investigation, evidence_list = run_investigation(db, request.question)
    
    answer = investigation.summary or "Could not synthesize an answer."
    
    return QueryResponse(
        answer=answer,
        evidence=evidence_list
    )

@router.get("/investigations/recent")
def get_recent_investigations(limit: int = 10, db: Session = Depends(get_db)):
    """
    Returns recent investigations executed by the system.
    """
    from models.investigations import Investigation
    invs = db.query(Investigation).order_by(Investigation.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(i.id),
            "query": i.query,
            "status": i.status,
            "summary": i.summary,
            "created_at": i.created_at.isoformat() if i.created_at else None
        }
        for i in invs
    ]
