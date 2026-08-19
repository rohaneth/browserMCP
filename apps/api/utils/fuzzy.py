import re
import difflib
from typing import List, Optional, Set, Dict, Tuple

# Common stop words used in natural language search queries
QUESTION_STOP_WORDS = {
    "did", "do", "does", "have", "has", "had", "was", "were", "is", "am", "are",
    "i", "me", "my", "myself", "we", "our", "you", "your",
    "search", "searched", "searching", "look", "looked", "looking", "lookup", "find",
    "visit", "visited", "visiting", "watch", "watched", "watching", "view", "viewed",
    "type", "typed", "typing", "input", "inputs", "ask", "asked", "asking",
    "about", "for", "any", "anything", "what", "which", "how", "why", "when", "where",
    "the", "a", "an", "on", "in", "at", "to", "of", "and", "or", "from", "with",
    "before", "recently", "online", "yesterday", "today", "history", "browser"
}


def normalize_string(text: str) -> str:
    """
    Cleans, lowercases, and strips punctuation/excessive whitespace from a string.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract_fuzzy_keywords(query: str) -> List[str]:
    """
    Extracts significant content words from a query, eliminating question stop words.
    """
    cleaned = normalize_string(query)
    words = cleaned.split()
    return [w for w in words if w not in QUESTION_STOP_WORDS and len(w) >= 2]


def calculate_token_overlap_score(target_text: str, candidate_text: str) -> float:
    """
    Calculates Jaccard/containment token overlap between target query and candidate text.
    """
    if not target_text or not candidate_text:
        return 0.0
    
    t_norm = normalize_string(target_text)
    c_norm = normalize_string(candidate_text)

    # Direct substring containment gives high score
    if t_norm in c_norm or c_norm in t_norm:
        return 0.95

    t_tokens = set(extract_fuzzy_keywords(target_text))
    c_tokens = set(extract_fuzzy_keywords(candidate_text))

    if not t_tokens or not c_tokens:
        return 0.0

    intersection = t_tokens.intersection(c_tokens)
    if not intersection:
        # Check character-level fuzzy similarity on single key tokens
        max_ratio = 0.0
        for t in t_tokens:
            for c in c_tokens:
                ratio = difflib.SequenceMatcher(None, t, c).ratio()
                if ratio > max_ratio:
                    max_ratio = ratio
        return max_ratio if max_ratio >= 0.75 else 0.0

    return len(intersection) / len(t_tokens)


def find_entity_matches_in_text(entity: str, text: str, threshold: float = 0.75) -> Tuple[bool, float]:
    """
    Checks if an entity or close typographical variant appears in target text.
    Handles typos like 'dostovesky' -> 'dostoevsky', 'avanger' -> 'avengers'.
    """
    if not entity or not text:
        return False, 0.0

    e_clean = normalize_string(entity)
    t_clean = normalize_string(text)

    # 1. Exact Substring Match
    if e_clean in t_clean:
        return True, 1.0

    e_words = e_clean.split()
    t_words = t_clean.split()

    if not e_words or not t_words:
        return False, 0.0

    # 2. Multi-word Substring / Window Match
    n = len(e_words)
    if n > 1:
        for i in range(len(t_words) - n + 1):
            window = " ".join(t_words[i:i+n])
            ratio = difflib.SequenceMatcher(None, e_clean, window).ratio()
            if ratio >= threshold:
                return True, ratio

    # 3. Single-word Fuzzy Match
    for e_w in e_words:
        for t_w in t_words:
            ratio = difflib.SequenceMatcher(None, e_w, t_w).ratio()
            if ratio >= threshold:
                return True, ratio

    return False, 0.0
