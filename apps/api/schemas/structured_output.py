from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    CONFIRMED = "CONFIRMED"
    LIKELY = "LIKELY"
    NOT_FOUND = "NOT_FOUND"
    UNCERTAIN = "UNCERTAIN"


class Citation(BaseModel):
    event_id: str
    timestamp: Optional[datetime] = None
    url: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    score: float = 1.0


class StructuredToolCall(BaseModel):
    step_number: int
    tool_name: str
    parameters: Dict[str, Any]
    thought_rationale: str
    observation_summary: Optional[str] = None
    evidence_count_gained: int = 0


class AgenticInvestigationTrace(BaseModel):
    query: str
    total_steps: int
    tools_used: List[str]
    step_history: List[StructuredToolCall]
    stop_reason: str  # e.g. "sufficient_evidence", "max_iterations_reached", "no_new_evidence"


class StructuredInvestigationOutput(BaseModel):
    query: str
    confidence: ConfidenceLevel
    direct_answer: str
    key_findings: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    trace: Optional[AgenticInvestigationTrace] = None
    structured_metadata: Dict[str, Any] = Field(default_factory=dict)


class MLClassificationResult(BaseModel):
    category: str
    confidence: float
    probabilities: Dict[str, float]
    features_used: List[str] = Field(default_factory=list)


class InterestClusterResult(BaseModel):
    cluster_id: int
    label: str
    top_keywords: List[str]
    event_count: int
    representative_urls: List[str]
    coherence_score: float


class BehavioralAnomalyResult(BaseModel):
    is_anomaly: bool
    anomaly_score: float  # higher = more anomalous (0 to 1)
    anomaly_reasons: List[str]
    unusual_dimensions: Dict[str, Any]
    event_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class ContentRecommendationItem(BaseModel):
    topic: str
    rationale: str
    relevance_score: float
    category: str
    related_interests: List[str]
