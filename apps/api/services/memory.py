import logging
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from models.events import Event
from models.memories import Memory, MemoryEvidence
from models.sessions import BrowserSession as SessionModel

logger = logging.getLogger(__name__)

import os

def generate_embedding(text: str) -> List[float]:
    embedding = [0.0] * 384
    if text:
        for i, char in enumerate(text[:384]):
            embedding[i] = float((ord(char) * 17) % 100) / 100.0
    return embedding

# Task 5.2: Memory Extraction
def extract_memories_from_session(db: Session, session_id: UUID) -> List[Memory]:
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        return []

    events = db.query(Event).filter(Event.session_id == session_id).order_by(Event.timestamp).all()
    if not events:
        return []

    # Basic extraction: finding search events to form facts.
    # Phase 5 calls for LLM usage later, but starting deterministic.
    search_events = [e for e in events if e.event_type == 'search_submitted']
    
    memories = []
    for se in search_events:
        content = f"User searched for: {se.input_text or se.page_title}"
        memory = Memory(
            content=content,
            embedding=generate_embedding(content),
            embedding_model="mock-all-MiniLM-L6-v2",
            type="FACT"
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        evidence = MemoryEvidence(
            memory_id=memory.id,
            event_id=se.event_id
        )
        db.add(evidence)
        db.commit()
        
        memories.append(memory)
        
    return memories

# Task 5.5: Semantic Search
def search_similar_memories(db: Session, query: str, limit: int = 5) -> List[Memory]:
    query_embedding = generate_embedding(query)
    
    is_sqlite = db.bind.dialect.name == "sqlite"
    
    if is_sqlite:
        import math
        memories = db.query(Memory).all()
        if not memories:
            return []
            
        def l2_dist(v1, v2):
            if not v1 or not v2: return 999.0
            if isinstance(v1, str):
                import json
                try: v1 = json.loads(v1)
                except: return 999.0
            if len(v1) != len(v2): return 999.0
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

        memories.sort(key=lambda m: l2_dist(m.embedding, query_embedding))
        return memories[:limit]
    else:
        # using pgvector L2 distance operator `<->`
        results = db.query(Memory).order_by(Memory.embedding.l2_distance(query_embedding)).limit(limit).all()
        return results
