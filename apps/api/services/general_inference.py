import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from collections import Counter
from sqlalchemy.orm import Session

from models.events import Event
from utils.normalization import extract_url_search_params
from utils.fuzzy import normalize_string, extract_fuzzy_keywords, find_entity_matches_in_text

logger = logging.getLogger(__name__)

# Core known semantic anchors for common categories, extensible dynamically
SEMANTIC_CLUSTERS: Dict[str, Dict[str, List[str]]] = {
    "personality_social": {
        "Introversion / Solitary / Quiet": [
            "introvert", "introversion", "alone", "solo", "quiet", "solitary",
            "living alone", "travel alone", "by myself", "without partner",
            "without partying", "stay inside", "indoors", "peaceful"
        ],
        "Extroversion / Social / High-Stimulation": [
            "extrovert", "extroversion", "party", "parties", "club", "clubs",
            "nightlife", "group", "socialize", "meet people", "networking", "crowd"
        ]
    },
    "environment": {
        "Urban / City Living": [
            "city", "cities", "pune", "bangalore", "metro", "urban",
            "rent", "pg", "software developer career", "living expenses"
        ],
        "Rural / Nature / Countryside": [
            "rural", "village", "countryside", "nature", "mountains", "hills", "farm", "scenic"
        ]
    },
    "medium_preference": {
        "Video / Film Watching": [
            "movie", "movies", "film", "watch", "youtube", "video", "cinema", "thriller", "action"
        ],
        "Text / Reading / Literature": [
            "book", "books", "read", "reading", "author", "authors", "goodreads", "article", "novel"
        ]
    },
    "mindset": {
        "Theoretical / Philosophical": [
            "philosophy", "philosophical", "meaning of life", "morality", "free will",
            "camus", "nietzsche", "krishnamurti", "osho", "observer", "existential"
        ],
        "Practical / Career / Applied": [
            "salary", "resume", "roadmap", "job", "freelancing", "spring boot",
            "interview", "exam", "questions", "budget", "expenses", "saving", "food", "cook"
        ]
    }
}


class GeneralInferenceEngine:
    """
    Generalized inference engine that evaluates binary or multi-hypothesis questions
    (e.g., Introvert vs Extrovert, City vs Rural, Watching vs Reading, Philosophy vs Programming).
    Discovers evidence across complete browser dataset and calculates comparative support.
    """

    @classmethod
    def detect_inference_question(cls, query: str) -> Optional[Dict[str, Any]]:
        q_norm = normalize_string(query)

        # 1. Binary Choice / Contrast Pattern (A or B, A vs B, prefer A or B)
        # e.g., "Am I introvert or extrovert?", "Do I prefer cities or rural places?", "philosophy or programming"
        contrast_match = re.search(r'\b(?:am\s+i|do\s+i\s+prefer|are\s+we|more\s+interested\s+in|choose\s+between)\s+(.+?)\s+(?:or|vs|versus)\s+(.+)', q_norm)
        if contrast_match:
            side_a = contrast_match.group(1).strip().replace("prefer", "").replace("interested in", "").strip()
            side_b = contrast_match.group(2).strip().rstrip("?").strip()
            return {
                "type": "contrast",
                "hypothesis_a": side_a,
                "hypothesis_b": side_b
            }

        # 2. Direct Concept Analysis (e.g., "Am I an introvert?", "Am I extroverted?")
        if any(w in q_norm for w in ["introvert", "introversion", "extrovert", "extroversion"]):
            return {
                "type": "contrast",
                "hypothesis_a": "introvert",
                "hypothesis_b": "extrovert"
            }

        if any(w in q_norm for w in ["city or rural", "cities or rural", "urban or rural"]):
            return {
                "type": "contrast",
                "hypothesis_a": "city living",
                "hypothesis_b": "rural places"
            }

        if any(w in q_norm for w in ["watching or reading", "movies or reading", "watch or read", "film or books"]):
            return {
                "type": "contrast",
                "hypothesis_a": "watching movies / videos",
                "hypothesis_b": "reading books / literature"
            }

        if any(w in q_norm for w in ["practical or theoretical", "theory or practice"]):
            return {
                "type": "contrast",
                "hypothesis_a": "practical / applied tasks",
                "hypothesis_b": "theoretical / philosophical ideas"
            }

        return None

    @classmethod
    def get_related_concept_keywords(cls, hypothesis: str) -> List[str]:
        h_norm = normalize_string(hypothesis)
        keywords = set(extract_fuzzy_keywords(hypothesis))

        # Check clusters for relevant keywords
        for cluster_group in SEMANTIC_CLUSTERS.values():
            for cluster_name, kws in cluster_group.items():
                c_norm = normalize_string(cluster_name)
                if any(w in c_norm for w in h_norm.split()) or any(w in h_norm for w in c_norm.split()):
                    keywords.update([k.lower() for k in kws])

        # Add single word stems
        for w in h_norm.split():
            if len(w) >= 3:
                keywords.add(w)
                if w.endswith("ing"): keywords.add(w[:-3])
                if w.endswith("s"): keywords.add(w[:-1])

        return list(keywords)

    @classmethod
    def evaluate_contrast_hypotheses(
        cls, db: Session, query: str, hypothesis_a: str, hypothesis_b: str
    ) -> Tuple[Dict[str, Any], List[Event]]:
        all_events = db.query(Event).all()

        kws_a = cls.get_related_concept_keywords(hypothesis_a)
        kws_b = cls.get_related_concept_keywords(hypothesis_b)

        events_a: List[Tuple[Event, float, str]] = []
        events_b: List[Tuple[Event, float, str]] = []

        seen_a = set()
        seen_b = set()

        for e in all_events:
            inp = e.input_text or extract_url_search_params(e.url) or ""
            title = e.page_title or ""
            url = e.url or ""
            text_corpus = f"{inp} {title} {url}".lower()

            # Score Hypothesis A
            score_a = 0.0
            matched_reason_a = ""
            for kw in kws_a:
                if kw in inp.lower():
                    score_a += 3.0
                    matched_reason_a = f"Search: '{inp}'"
                    break
                elif kw in title.lower():
                    score_a += 1.5
                    matched_reason_a = f"Page Title: '{title[:50]}'"
                    break
                elif kw in url.lower():
                    score_a += 0.5
                    matched_reason_a = f"URL: '{url[:50]}'"
                    break

            if score_a > 0 and str(e.event_id) not in seen_a:
                seen_a.add(str(e.event_id))
                events_a.append((e, score_a, matched_reason_a))

            # Score Hypothesis B
            score_b = 0.0
            matched_reason_b = ""
            for kw in kws_b:
                if kw in inp.lower():
                    score_b += 3.0
                    matched_reason_b = f"Search: '{inp}'"
                    break
                elif kw in title.lower():
                    score_b += 1.5
                    matched_reason_b = f"Page Title: '{title[:50]}'"
                    break
                elif kw in url.lower():
                    score_b += 0.5
                    matched_reason_b = f"URL: '{url[:50]}'"
                    break

            if score_b > 0 and str(e.event_id) not in seen_b:
                seen_b.add(str(e.event_id))
                events_b.append((e, score_b, matched_reason_b))

        total_score_a = sum(s for _, s, _ in events_a)
        total_score_b = sum(s for _, s, _ in events_b)

        # Classify winner
        if total_score_a > total_score_b * 1.3:
            winner = hypothesis_a
            margin = "strong" if total_score_a > total_score_b * 2.0 else "moderate"
        elif total_score_b > total_score_a * 1.3:
            winner = hypothesis_b
            margin = "strong" if total_score_b > total_score_a * 2.0 else "moderate"
        elif total_score_a > 0 or total_score_b > 0:
            winner = "Balanced / Dual Interest"
            margin = "even"
        else:
            winner = "Insufficient Data"
            margin = "none"

        combined_events: List[Event] = [e for e, _, _ in events_a] + [e for e, _, _ in events_b]

        inference_summary = {
            "query": query,
            "hypothesis_a": hypothesis_a,
            "hypothesis_b": hypothesis_b,
            "score_a": round(total_score_a, 1),
            "score_b": round(total_score_b, 1),
            "count_a": len(events_a),
            "count_b": len(events_b),
            "winner": winner,
            "margin": margin,
            "samples_a": [f"{r} at {e.timestamp}" for e, _, r in events_a[:5]],
            "samples_b": [f"{r} at {e.timestamp}" for e, _, r in events_b[:5]]
        }

        return inference_summary, combined_events
