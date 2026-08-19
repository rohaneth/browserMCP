import uuid
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from .base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_id = Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Event type as a string rather than an ENUM to avoid migration friction when adding types
    event_type = Column(String(50), nullable=False, index=True)

    url = Column(String(10000), nullable=True)
    canonical_url = Column(String(2048), nullable=True)
    domain = Column(String(255), nullable=True, index=True)
    page_title = Column(String(1000), nullable=True)

    content = Column(Text, nullable=True)
    input_text = Column(Text, nullable=True)

    # Ensure JSONB is used for efficient querying and indexing of arbitrary metadata
    metadata_ = Column("metadata", JSONB, nullable=True)

    source = Column(String(100), nullable=False)
    schema_version = Column(Integer, nullable=False, default=1)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Task 3.3: Session assignment
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
