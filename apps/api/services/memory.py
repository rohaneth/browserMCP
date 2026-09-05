import logging
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from models.events import Event
from models.memories import Memory, MemoryEvidence
from models.sessions import BrowserSession as SessionModel
from services.embeddings import embed_text, embed_batch
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)


def generate_embedding(text: str) -> List[float]:
    """Generates 384-dimensional dense semantic embedding."""
    return embed_text(text)


def extract_memories_from_session(db: Session, session_id: UUID) -> List[Memory]:
    """
    Extracts atomic memories from session events and indexes with real dense embeddings.
    """
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        return []

    events = db.query(Event).filter(Event.session_id == session_id).order_by(Event.timestamp).all()
    if not events:
        return []

    search_events = [e for e in events if e.event_type in ('search_submitted', 'page_loaded')]
    if not search_events:
        return []

    items_to_index = []
    event_mapping = []

    for se in search_events[:10]:
        title = se.page_title or ""
        inp = se.input_text or ""
        content = f"User searched or viewed: {inp or title} on {se.domain or 'web'}"
        items_to_index.append({"content": content, "type": "FACT"})
        event_mapping.append(se)

    created_memories = VectorStore.index_texts(db, items_to_index)

    # Link evidence junction
    for mem, se in zip(created_memories, event_mapping):
        evidence = MemoryEvidence(
            memory_id=mem.id,
            event_id=se.event_id
        )
        db.add(evidence)
    db.commit()

    return created_memories


def search_similar_memories(db: Session, query: str, limit: int = 5) -> List[Memory]:
    """
    Real vector similarity search using cosine distance / pgvector.
    """
    scored_results = VectorStore.search_similar(db, query, limit=limit)
    return [mem for mem, score in scored_results]
