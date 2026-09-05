import logging
import numpy as np
from typing import List, Dict, Any, Optional
from collections import Counter
from sklearn.cluster import MiniBatchKMeans, DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session
from models.events import Event
from services.embeddings import embed_batch
from schemas.structured_output import InterestClusterResult

logger = logging.getLogger(__name__)


class InterestClusterEngine:
    """
    Unsupervised ML pipeline for discovering semantic interest clusters.
    Pipeline: Browser Events -> Dense Embeddings -> K-Means / DBSCAN Clustering
              -> TF-IDF cluster keyword extraction -> Named Interest Profiles.
    """

    @classmethod
    def discover_clusters(
        cls,
        db: Session,
        n_clusters: int = 5,
        min_samples: int = 3
    ) -> List[InterestClusterResult]:
        events = db.query(Event).all()
        if not events:
            return []

        # Prepare corpus texts
        corpus = []
        valid_events = []
        for e in events:
            txt = f"{e.page_title or ''} {e.input_text or ''} {e.domain or ''} {e.content or ''}".strip()
            if len(txt) >= 5:
                corpus.append(txt)
                valid_events.append(e)

        if len(valid_events) < min_samples:
            return []

        # Step 1: Generate embeddings for all events
        embeddings = np.array(embed_batch(corpus), dtype=np.float32)

        # Step 2: Determine appropriate cluster count
        actual_k = min(n_clusters, len(valid_events) // 2 or 1)
        if actual_k < 2:
            actual_k = 1

        # Step 3: Run K-Means Clustering
        kmeans = MiniBatchKMeans(n_clusters=actual_k, random_state=42, batch_size=100, n_init=3)
        cluster_labels = kmeans.fit_predict(embeddings)

        # Step 4: Extract Cluster Topics using TF-IDF
        results: List[InterestClusterResult] = []
        
        # Calculate cluster coherence (mean distance to cluster center)
        for cluster_id in range(actual_k):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            if len(cluster_indices) == 0:
                continue

            cluster_texts = [corpus[i] for i in cluster_indices]
            cluster_events = [valid_events[i] for i in cluster_indices]
            
            # TF-IDF keyword extraction for this cluster
            try:
                tfidf = TfidfVectorizer(max_features=10, stop_words='english', ngram_range=(1, 2))
                tfidf_mat = tfidf.fit_transform(cluster_texts)
                top_words = list(tfidf.get_feature_names_out())
            except Exception:
                # Fallback word counter
                words = " ".join(cluster_texts).lower().split()
                counts = Counter([w for w in words if len(w) > 3])
                top_words = [w for w, _ in counts.most_common(5)]

            # Generate natural cluster label
            primary_label = " & ".join([w.title() for w in top_words[:3]]) if top_words else f"Cluster {cluster_id}"
            
            # Top representative URLs
            rep_urls = [e.url for e in cluster_events if e.url][:5]
            
            # Coherence calculation (average cosine similarity to centroid)
            cluster_vecs = embeddings[cluster_indices]
            centroid = kmeans.cluster_centers_[cluster_id]
            c_norm = np.linalg.norm(centroid)
            if c_norm > 0:
                dots = np.dot(cluster_vecs, centroid) / (np.linalg.norm(cluster_vecs, axis=1) * c_norm + 1e-9)
                coherence = float(np.mean(dots))
            else:
                coherence = 1.0

            results.append(InterestClusterResult(
                cluster_id=cluster_id,
                label=primary_label,
                top_keywords=top_words[:8],
                event_count=len(cluster_events),
                representative_urls=rep_urls,
                coherence_score=round(coherence, 4)
            ))

        # Sort by event count descending
        results.sort(key=lambda x: x.event_count, reverse=True)
        return results
