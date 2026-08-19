import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .base import Base


class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)

    # 384 dimensions corresponds to HuggingFace all-MiniLM-L6-v2
    embedding = Column(Vector(384), nullable=True)

    # Model provenance
    embedding_model = Column(String(100), nullable=True)
    embedding_model_version = Column(String(50), nullable=True)

    # FACT vs INFERENCE
    type = Column(String(50), nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MemoryEvidence(Base):
    __tablename__ = "memory_evidence"

    # Using UUIDs as the primary key for the junction
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    memory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key directly to the canonical event_id in the events table
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
