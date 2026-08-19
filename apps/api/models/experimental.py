import uuid
from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from models.base import Base

class WatcherState(Base):
    __tablename__ = "experimental_watcher_state"

    id = Column(Integer, primary_key=True, default=1)
    is_running = Column(Boolean, nullable=False, default=False)
    last_processed_event_id = Column(UUID(as_uuid=True), nullable=True)
    last_processed_timestamp = Column(DateTime(timezone=True), nullable=True)
    total_events_observed = Column(Integer, nullable=False, default=0)
    total_alerts_triggered = Column(Integer, nullable=False, default=0)
    active_focus = Column(String(255), nullable=True) # e.g. "Interest change monitoring"
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class WatcherAlert(Base):
    __tablename__ = "experimental_watcher_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(100), nullable=False) # e.g. "interest_shift", "activity_burst", "new_topic"
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    supporting_event_ids = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class DiscoveryRun(Base):
    __tablename__ = "experimental_discovery_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(50), nullable=False, default="started") # started, analyzing, completed, failed
    focus_hint = Column(String(255), nullable=True)
    hypotheses_generated = Column(Integer, nullable=False, default=0)
    hypotheses_confirmed = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class DiscoveryResult(Base):
    __tablename__ = "experimental_discovery_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("experimental_discovery_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False) # "emerging_interest", "unusual_pattern", "workflow_habit", "temporal_shift"
    hypothesis = Column(Text, nullable=False)
    confidence = Column(String(50), nullable=False) # "CONFIRMED", "LIKELY", "SPECULATIVE"
    narrative = Column(Text, nullable=False)
    supporting_evidence = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
