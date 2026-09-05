import os
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from schemas.search import Evidence
from services.embeddings import embed_text, embed_batch

logger = logging.getLogger(__name__)


class NeuralReranker:
    """
    Bi-encoder semantic vector reranker for candidate retrieval.
    Re-scores and re-ranks candidate evidence records against the query embedding
    to prioritize semantic alignment over raw keyword match counts.
    (Note: uses dense vector cosine scoring; not a transformer cross-attention layer).
    """

    @classmethod
    def is_enabled(cls) -> bool:
        val = os.getenv("RERANKER_ENABLED", "true").lower()
        return val in ("1", "true", "yes", "on")

    @classmethod
    def rerank_evidence(
        cls,
        query: str,
        candidates: List[Evidence],
        top_n: int = 15
    ) -> List[Evidence]:
        if not candidates or not cls.is_enabled():
            return candidates[:top_n]

        query_vec = np.array(embed_text(query), dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)
        if q_norm == 0:
            return candidates[:top_n]

        # Extract text representations for candidates
        candidate_texts = [
            f"{c.title or ''} {c.snippet or ''} {c.url or ''}".strip()
            for c in candidates
        ]
        
        cand_vecs = np.array(embed_batch(candidate_texts), dtype=np.float32)
        
        # Calculate semantic cosine alignment
        c_norms = np.linalg.norm(cand_vecs, axis=1, keepdims=True)
        c_norms[c_norms == 0.0] = 1.0
        normalized_cands = cand_vecs / c_norms
        
        # Dot product with normalized query
        normalized_query = query_vec / q_norm
        semantic_scores = np.dot(normalized_cands, normalized_query)

        # Combine with initial relevance score (85% semantic cross-score + 15% initial retrieval weight)
        reranked_tuples: List[Tuple[Evidence, float]] = []
        for i, cand in enumerate(candidates):
            sem_score = float(semantic_scores[i])
            initial_score = float(cand.relevance or 0.5)
            combined_score = (0.85 * sem_score) + (0.15 * initial_score)
            
            # Update evidence relevance
            cand.relevance = round(combined_score, 4)
            reranked_tuples.append((cand, combined_score))

        # Sort descending by combined rerank score
        reranked_tuples.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in reranked_tuples[:top_n]]
