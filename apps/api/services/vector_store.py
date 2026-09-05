import json
import logging
import numpy as np
from typing import List, Tuple, Optional, Any, Dict
from sqlalchemy.orm import Session
from sklearn.neighbors import NearestNeighbors
from models.memories import Memory
from services.embeddings import embed_text, embed_batch

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector search interface supporting fast spatial neighborhood tree indexing
    (NearestNeighbors with cosine/euclidean metrics), PostgreSQL pgvector,
    and exact NumPy cosine similarity fallback.
    """

    @classmethod
    def search_similar(
        cls,
        db: Session,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.0
    ) -> List[Tuple[Memory, float]]:
        """
        Retrieves top similar memory vectors using NearestNeighbors spatial index
        or exact cosine fallback.
        Returns list of (Memory, similarity_score) tuples sorted in descending order.
        """
        query_vec = np.array(embed_text(query), dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)
        if q_norm == 0:
            return []

        # Check if database dialect is postgres with pgvector
        is_postgres = db.bind and db.bind.dialect.name == "postgresql"

        if is_postgres:
            try:
                memories = (
                    db.query(Memory)
                    .filter(Memory.embedding != None)
                    .order_by(Memory.embedding.cosine_distance(query_vec.tolist()))
                    .limit(limit)
                    .all()
                )
                return [(m, 1.0) for m in memories]
            except Exception as e:
                logger.warning(f"PostgreSQL pgvector query failed: {e}. Falling back to spatial index.")

        # Local Vector Indexing Engine
        all_memories = db.query(Memory).all()
        if not all_memories:
            return []

        scored_items: List[Tuple[Memory, float]] = []
        
        valid_memories = []
        valid_vectors = []

        for mem in all_memories:
            raw_emb = mem.embedding
            if not raw_emb:
                continue

            if isinstance(raw_emb, str):
                try:
                    vec = json.loads(raw_emb)
                except Exception:
                    continue
            elif isinstance(raw_emb, (list, tuple)):
                vec = raw_emb
            else:
                try:
                    vec = list(raw_emb)
                except Exception:
                    continue

            vec_arr = np.array(vec, dtype=np.float32)
            v_norm = np.linalg.norm(vec_arr)
            if v_norm == 0:
                continue
            valid_memories.append(mem)
            valid_vectors.append(vec_arr / v_norm)

        if not valid_vectors:
            return []

        # Use NearestNeighbors with cosine metric
        try:
            X = np.array(valid_vectors, dtype=np.float32)
            n_k = min(limit, len(valid_memories))
            nn = NearestNeighbors(n_neighbors=n_k, metric="cosine", algorithm="auto")
            nn.fit(X)
            
            q_normed = (query_vec / q_norm).reshape(1, -1)
            distances, indices = nn.kneighbors(q_normed)
            
            results: List[Tuple[Memory, float]] = []
            for dist, idx in zip(distances[0], indices[0]):
                sim = 1.0 - float(dist)
                if sim >= min_similarity:
                    results.append((valid_memories[idx], round(sim, 4)))
            return results
        except Exception as e:
            logger.warning(f"NearestNeighbors indexing failed: {e}. Using exact dot-product.")
            X = np.array(valid_vectors, dtype=np.float32)
            q_normed = query_vec / q_norm
            sims = np.dot(X, q_normed)
            scored = [(valid_memories[i], float(sims[i])) for i in range(len(valid_memories)) if sims[i] >= min_similarity]
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:limit]

    @classmethod
    def index_texts(
        cls,
        db: Session,
        items: List[Dict[str, Any]]
    ) -> List[Memory]:
        """
        Batch embeds and indexes texts into the Memory store.
        """
        if not items:
            return []

        contents = [item["content"] for item in items]
        vectors = embed_batch(contents)

        created_memories = []
        for item, vec in zip(items, vectors):
            mem = Memory(
                content=item["content"],
                embedding=vec,
                embedding_model="dense-semantic-384",
                type=item.get("type", "FACT")
            )
            db.add(mem)
            created_memories.append(mem)

        db.commit()
        for mem in created_memories:
            db.refresh(mem)

        return created_memories
