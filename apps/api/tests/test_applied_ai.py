import pytest
import os
import sys
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from db.session import SessionLocal
from services.embeddings import embed_text, embed_batch, get_embedding_provider
from services.vector_store import VectorStore
from services.reranker import NeuralReranker
from services.classifier import BrowserEventClassifier
from services.clustering import InterestClusterEngine
from services.anomaly_detection import BehavioralAnomalyDetector
from services.recommendation import RecommendationEngine
from services.agentic_investigator import AgenticInvestigator
from schemas.search import Evidence
from schemas.structured_output import ConfidenceLevel


@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_real_embeddings_generation():
    """Test 1: Real Dense Embedding Provider outputs correct dimensions."""
    vec = embed_text("FastAPI backend testing with python")
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert any(abs(v) > 0.0 for v in vec)

    batch_vecs = embed_batch(["Python coding", "PostgreSQL database optimization"])
    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 384
    assert len(batch_vecs[1]) == 384


def test_vector_store_search(db_session: Session):
    """Test 2: VectorStore indexing and cosine similarity search."""
    results = VectorStore.search_similar(db_session, query="python development", limit=3)
    assert isinstance(results, list)


def test_neural_reranker():
    """Test 3: Neural Cross-Reranker re-scores candidates semantically."""
    from datetime import datetime
    cands = [
        Evidence(event_id="e-1", timestamp=datetime.utcnow(), url="https://cooking.com", title="Baking Bread", snippet="recipe", relevance=0.8),
        Evidence(event_id="e-2", timestamp=datetime.utcnow(), url="https://github.com", title="Python FastAPI Repository", snippet="backend api code", relevance=0.4)
    ]
    reranked = NeuralReranker.rerank_evidence(
        query="python web framework",
        candidates=cands,
        top_n=2
    )
    assert len(reranked) == 2
    # The python repository should be ranked #1 after semantic reranking
    assert "github" in reranked[0].url.lower() or "python" in reranked[0].title.lower()


def test_ml_event_classifier():
    """Test 4: ML Event Classifier accurately predicts target categories and probabilities."""
    res_code = BrowserEventClassifier.classify(
        text="how to fix type error in typescript function react component",
        domain="stackoverflow.com"
    )
    assert res_code.category == "programming/development"
    assert res_code.confidence > 0.3
    assert "programming/development" in res_code.probabilities

    res_shop = BrowserEventClassifier.classify(
        text="buy wireless noise cancelling headphones discount price checkout",
        domain="amazon.com"
    )
    assert res_shop.category == "shopping"
    assert res_shop.confidence > 0.3


def test_interest_clustering(db_session: Session):
    """Test 5: Unsupervised interest clustering."""
    clusters = InterestClusterEngine.discover_clusters(db_session, n_clusters=3, min_samples=2)
    assert isinstance(clusters, list)
    if clusters:
        assert hasattr(clusters[0], "cluster_id")
        assert hasattr(clusters[0], "top_keywords")
        assert hasattr(clusters[0], "coherence_score")


def test_behavioral_anomaly_detection(db_session: Session):
    """Test 6: ML Behavioral Anomaly Detection with Isolation Forest."""
    anomalies = BehavioralAnomalyDetector.detect_anomalies(db_session, contamination=0.1, limit=5)
    assert isinstance(anomalies, list)


def test_content_recommendation_engine(db_session: Session):
    """Test 7: Content-based recommendation engine."""
    recs = RecommendationEngine.get_recommendations(db_session, limit=3)
    assert isinstance(recs, list)
    if recs:
        assert hasattr(recs[0], "topic")
        assert hasattr(recs[0], "relevance_score")
        assert hasattr(recs[0], "category")


def test_agentic_investigation_loop(db_session: Session):
    """Test 8: Agentic multi-step investigator produces structured output and trace."""
    structured_out = AgenticInvestigator.run_agentic_loop(
        db=db_session,
        query="What did I research about Python or Java?",
        max_iterations=3
    )
    assert structured_out.query is not None
    assert structured_out.confidence in [ConfidenceLevel.CONFIRMED, ConfidenceLevel.LIKELY, ConfidenceLevel.NOT_FOUND]
    assert structured_out.direct_answer is not None
    assert structured_out.trace is not None
    assert structured_out.trace.total_steps >= 1
    assert len(structured_out.trace.step_history) >= 1


def test_lyzr_agent_orchestrator(db_session: Session):
    """Test 9: Lyzr AI Agent Orchestrator coordinates multi-route investigation and citations."""
    from services.lyzr_agent import LyzrAgentOrchestrator
    
    # Test with LYZR enabled
    os.environ["LYZR_ENABLED"] = "true"
    os.environ["LYZR_API_KEY"] = "sk-default-rzLQezfTajH4WZloisf9BrcnyM3INCr8"
    assert LyzrAgentOrchestrator.is_enabled() is True

    out = LyzrAgentOrchestrator.run_agent(
        db=db_session,
        query="What is my favourite programming language?"
    )
    assert out.query is not None
    assert out.confidence in [ConfidenceLevel.CONFIRMED, ConfidenceLevel.LIKELY, ConfidenceLevel.NOT_FOUND]
    assert len(out.citations) > 0
    assert out.trace is not None
    assert "generalized_investigation_orchestrator" in out.trace.tools_used

    # Test fallback when LYZR is disabled
    os.environ["LYZR_ENABLED"] = "false"
    assert LyzrAgentOrchestrator.is_enabled() is False
    fallback_out = LyzrAgentOrchestrator.run_agent(
        db=db_session,
        query="What is my favourite programming language?"
    )
    assert fallback_out.query is not None
    assert len(fallback_out.citations) > 0
    
    # Restore env
    os.environ["LYZR_ENABLED"] = "true"
