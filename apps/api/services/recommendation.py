import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.events import Event
from services.clustering import InterestClusterEngine
from services.embeddings import embed_text, embed_batch
from schemas.structured_output import ContentRecommendationItem

logger = logging.getLogger(__name__)

# Curated candidate exploration pool across common tech & knowledge domains
CANDIDATE_TOPIC_POOL = [
    {"topic": "Advanced PostgreSQL Indexing & EXPLAIN ANALYZE Optimization", "category": "programming/development", "keywords": ["postgres", "sql", "index", "performance", "database"]},
    {"topic": "Building High-Throughput Microservices with FastAPI & AsyncIO", "category": "programming/development", "keywords": ["fastapi", "python", "backend", "async", "api"]},
    {"topic": "Rust Concurrency Patterns: Channels, Mutexes, and Atomics", "category": "programming/development", "keywords": ["rust", "concurrency", "systems", "memory", "thread"]},
    {"topic": "Modern Frontend State Management with React 19 & Server Actions", "category": "programming/development", "keywords": ["react", "frontend", "javascript", "typescript", "ui"]},
    {"topic": "Deep Dive into Vector Databases & Approximate Nearest Neighbor Algorithms (HNSW)", "category": "research", "keywords": ["vector", "embeddings", "ai", "hnsw", "search"]},
    {"topic": "Albert Camus & Absurdism: Freedom and Rebellion in Modern Life", "category": "philosophy", "keywords": ["camus", "existentialism", "philosophy", "stranger", "meaning"]},
    {"topic": "Practical Machine Learning Systems Engineering & Model Monitoring", "category": "education", "keywords": ["machine learning", "ml", "pipeline", "monitoring", "evaluation"]},
    {"topic": "System Design: Scaling Distributed Event Streaming with Apache Kafka", "category": "programming/development", "keywords": ["kafka", "streaming", "distributed", "event", "scale"]},
    {"topic": "Epistemology & Cognitive Biases in Rational Decision Making", "category": "philosophy", "keywords": ["rational", "epistemology", "bias", "decision", "sagan"]}
]


class RecommendationEngine:
    """
    Content-based recommendation engine.
    Uses inferred user interest profiles & cluster centroids to score, rank, and suggest
    candidate research topics, documentation, and learning paths.
    """

    @classmethod
    def get_recommendations(
        cls,
        db: Session,
        limit: int = 5
    ) -> List[ContentRecommendationItem]:
        # 1. Discover active interest clusters
        clusters = InterestClusterEngine.discover_clusters(db, n_clusters=5)
        
        # Build user interest profile string
        user_interest_keywords = []
        for c in clusters:
            user_interest_keywords.extend(c.top_keywords)

        if not user_interest_keywords:
            # Fallback based on top domains/titles
            recent_events = db.query(Event).order_by(Event.timestamp.desc()).limit(30).all()
            for e in recent_events:
                if e.page_title:
                    user_interest_keywords.extend(e.page_title.lower().split()[:3])

        user_profile_text = " ".join(user_interest_keywords[:40]) if user_interest_keywords else "software development computer science"
        user_vec = np.array(embed_text(user_profile_text), dtype=np.float32)
        u_norm = np.linalg.norm(user_vec) or 1.0

        # 2. Embed candidate topics
        cand_texts = [f"{c['topic']} {' '.join(c['keywords'])}" for c in CANDIDATE_TOPIC_POOL]
        cand_vecs = np.array(embed_batch(cand_texts), dtype=np.float32)
        c_norms = np.linalg.norm(cand_vecs, axis=1, keepdims=True)
        c_norms[c_norms == 0.0] = 1.0
        normalized_cands = cand_vecs / c_norms

        # 3. Calculate cosine similarity
        similarities = np.dot(normalized_cands, user_vec / u_norm)

        # 4. Assemble recommendations
        ranked_indices = np.argsort(similarities)[::-1]
        
        recommendations = []
        for idx in ranked_indices[:limit]:
            cand = CANDIDATE_TOPIC_POOL[idx]
            sim = float(similarities[idx])
            
            # Formulate clear non-factual rationale
            cluster_match = [c.label for c in clusters if any(k in c.top_keywords for k in cand["keywords"])]
            rationale_str = (
                f"Recommended based on your recurring interest in {cluster_match[0]}"
                if cluster_match else
                f"High semantic alignment ({round(sim*100, 1)}%) with your active browsing topics."
            )

            recommendations.append(ContentRecommendationItem(
                topic=cand["topic"],
                rationale=rationale_str,
                relevance_score=round(sim, 4),
                category=cand["category"],
                related_interests=cand["keywords"][:4]
            ))

        return recommendations
