from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from db.session import get_db
from services.memory import search_similar_memories

router = APIRouter()

class MemorySearchResponse(BaseModel):
    id: str
    content: str
    type: str

@router.get("/memory/search", response_model=List[MemorySearchResponse])
def get_memory_search(
    query: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Semantic search over memories (Task 5.5).
    """
    results = search_similar_memories(db, query, limit)
    
    response = []
    for r in results:
        response.append(
            MemorySearchResponse(
                id=str(r.id),
                content=r.content,
                type=r.type
            )
        )
    return response
