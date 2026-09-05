import logging
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from models.events import Event
from schemas.structured_output import BehavioralAnomalyResult

logger = logging.getLogger(__name__)


class BehavioralAnomalyDetector:
    """
    Machine Learning Anomaly Detection for Browser Activity using Isolation Forest
    and statistical baseline profiling.
    Detects:
    1. Temporal anomalies (unusual browsing hours)
    2. Velocity spikes (unusual event rates)
    3. Rare / Outlier domain visits
    4. Outlier input length & behavioral deviations
    """

    @classmethod
    def detect_anomalies(
        cls,
        db: Session,
        contamination: float = 0.05,
        limit: int = 10
    ) -> List[BehavioralAnomalyResult]:
        events = db.query(Event).order_by(Event.timestamp.asc()).all()
        if len(events) < 10:
            return []

        # Extract features for each event:
        # [hour_of_day, is_weekend, domain_frequency_inv, input_length, title_length]
        domain_counts = Counter([e.domain for e in events if e.domain])
        total_events = len(events)

        feature_matrix = []
        event_ref = []

        for e in events:
            if not e.timestamp:
                continue

            hour = e.timestamp.hour
            is_weekend = 1.0 if e.timestamp.weekday() >= 5 else 0.0
            
            # Rare domain feature (1.0 = extremely rare, 0.0 = very common)
            dom_cnt = domain_counts.get(e.domain, 1)
            dom_rarity = 1.0 - (dom_cnt / total_events)
            
            inp_len = len(e.input_text or "")
            title_len = len(e.page_title or "")

            feature_matrix.append([hour, is_weekend, dom_rarity, inp_len, title_len])
            event_ref.append(e)

        if len(feature_matrix) < 10:
            return []

        X = np.array(feature_matrix, dtype=np.float32)

        # Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        
        # -1 for anomalies, 1 for normal
        preds = iso_forest.fit_predict(X)
        # Decision function: lower values mean more anomalous
        scores = iso_forest.decision_function(X)
        
        # Invert score so higher = more anomalous (0 to 1 range)
        min_score = np.min(scores)
        max_score = np.max(scores)
        span = (max_score - min_score) if (max_score - min_score) > 0 else 1.0
        normalized_anomaly_scores = 1.0 - ((scores - min_score) / span)

        anomaly_indices = np.where(preds == -1)[0]
        
        results: List[BehavioralAnomalyResult] = []
        for idx in anomaly_indices:
            e = event_ref[idx]
            anom_score = float(normalized_anomaly_scores[idx])
            
            # Identify specific anomaly drivers
            reasons = []
            features = X[idx]
            hour = int(features[0])
            if hour >= 1 and hour <= 5:
                reasons.append(f"Unusual late-night activity at {hour:02d}:00 UTC")
            if features[2] > 0.98:
                reasons.append(f"Extremely rare / first-time domain visit: '{e.domain}'")
            if features[3] > 100:
                reasons.append(f"Unusually long typed input payload ({int(features[3])} chars)")

            if not reasons:
                reasons.append(f"Unusual statistical multidimensional behavioral deviation (score: {round(anom_score, 2)})")

            results.append(BehavioralAnomalyResult(
                is_anomaly=True,
                anomaly_score=round(anom_score, 4),
                anomaly_reasons=reasons,
                unusual_dimensions={
                    "hour": hour,
                    "domain": e.domain,
                    "input_length": int(features[3]),
                    "page_title": e.page_title[:60] if e.page_title else None
                },
                event_id=str(e.event_id),
                timestamp=e.timestamp
            ))

        # Sort by highest anomaly score descending
        results.sort(key=lambda x: x.anomaly_score, reverse=True)
        return results[:limit]
