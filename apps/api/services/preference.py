import re
import difflib
import logging
from typing import Dict, Any, List, Tuple, Optional
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from models.events import Event
from schemas.search import Evidence
from utils.normalization import extract_url_search_params
from utils.fuzzy import normalize_string, extract_fuzzy_keywords, find_entity_matches_in_text

logger = logging.getLogger(__name__)

# Known programming language tokens for dynamic discovery across browser events
LANGUAGES = [
    "java", "python", "javascript", "typescript", "c++", "cpp", "rust",
    "golang", "go", "php", "ruby", "swift", "kotlin", "sql", "c#", "csharp",
    "html", "css", "assembly", "scala", "dart", "r", "julia"
]

KNOWN_ART_FORMS = [
    ("music", ["ukulele", "guitar", "instrument", "song", "headphones", "sound quality", "music", "spotify"]),
    ("literature", ["book", "books", "author", "authors", "novel", "novels", "goodreads", "camus", "nietzsche", "osho", "krishnamurti", "dostoevsky"]),
    ("film", ["movie", "movies", "film", "cinema", "thriller", "plot", "actor", "director", "cinematography"]),
    ("theatre & comedy", ["standup", "comedy show", "theatre", "theater", "comedy special", "roast"]),
    ("visual arts", ["painting", "drawing", "illustration", "sculpture", "sketch", "design"]),
    ("dance", ["dance", "ballet", "choreography"])
]

KNOWN_PHILOSOPHICAL_TRADITIONS = [
    ("Existentialism / Absurdism", ["camus", "nietzsche", "meaning of life", "the stranger", "absurd", "existential"]),
    ("Eastern Philosophy / Self-Inquiry", ["osho", "krishnamurti", "observer is the observed", "meditation", "awareness", "zen", "buddhis"]),
    ("Ethics & Moral Philosophy", ["morality", "free will", "sam harris", "ethics", "moral"]),
    ("Philosophy of Science / Rationalism", ["demon-haunted world", "sagan", "rational", "bayes", "epistemology"])
]


def detect_preference_category(query: str) -> Optional[str]:
    q_norm = normalize_string(query)

    # Typo-tolerant category keywords
    if any(k in q_norm for k in ["art form", "artform", "form of art", "which art", "arts"]):
        return "art_form"

    if any(k in q_norm for k in ["author", "authors", "writer", "writers", "novelist", "book", "books"]):
        return "authors_literature"

    if any(k in q_norm for k in ["philosoph", "tradition", "existential", "philosophy"]):
        return "philosophy"

    # Handle typos: 'langauge', 'progrmming', 'code', etc.
    if any(k in q_norm for k in ["programming language", "coding language", "preferred language", "language", "langauge", "coding"]):
        if any(w in q_norm for w in ["favourite", "favorite", "like", "prefer", "best", "use"]):
            return "programming_language"

    if any(k in q_norm for k in ["comedian", "standup", "stand up", "comedy show", "comic"]):
        return "comedian"

    if any(k in q_norm for k in ["movie", "movies", "kind of movies", "shows", "cinema", "film"]):
        if any(w in q_norm for w in ["favourite", "favorite", "like", "prefer", "best"]):
            return "movies_entertainment"

    if any(k in q_norm for k in ["topic", "topics", "interested in", "interests", "hobbies", "research"]):
        return "topics_interests"

    if any(k in q_norm for k in ["favourite", "favorite", "like most", "preferred"]):
        if any(w in q_norm for w in ["language", "langauge", "code", "tech", "coding"]):
            return "programming_language"
        if "art" in q_norm:
            return "art_form"
        if "author" in q_norm or "book" in q_norm:
            return "authors_literature"
        if "comedian" in q_norm or "funny" in q_norm:
            return "comedian"
        if "movie" in q_norm or "film" in q_norm or "video" in q_norm:
            return "movies_entertainment"
        return "general_preference"

    return None


def infer_programming_preference(db: Session) -> Tuple[Dict[str, Any], List[Event]]:
    """
    Scans entire database for programming language evidence across input_text, search params, page titles, URLs.
    Dynamically ranks candidate languages based on weighted signal frequency.
    """
    all_events = db.query(Event).all()

    candidate_scores: Dict[str, float] = {}
    candidate_queries: Dict[str, List[str]] = {}
    supporting_events: Dict[str, List[Event]] = {}

    for e in all_events:
        clean_url = re.sub(r'\.(html|css|js|php|json|xml)\b', '', e.url or '', flags=re.IGNORECASE)
        
        input_text = (e.input_text or "").strip()
        url_search = (extract_url_search_params(e.url) or "").strip()
        page_title = (e.page_title or "").strip()

        search_text = f"{input_text} {url_search}".lower()
        title_text = page_title.lower()
        url_text = clean_url.lower()

        for lang in LANGUAGES:
            pattern = r'\b' + re.escape(lang) + r'\b'
            
            lang_score = 0.0
            if re.search(pattern, search_text):
                lang_score += 5.0
            if re.search(pattern, title_text):
                lang_score += 2.0
            if re.search(pattern, url_text):
                lang_score += 1.0

            if lang_score > 0:
                display_name = lang.upper() if lang in ["sql", "html", "css", "php", "cpp"] else lang.capitalize()
                if lang == "c++" or lang == "cpp": display_name = "C++"
                if lang == "c#" or lang == "csharp": display_name = "C#"
                if lang == "js" or lang == "javascript": display_name = "JavaScript"
                if lang == "ts" or lang == "typescript": display_name = "TypeScript"

                candidate_scores[display_name] = candidate_scores.get(display_name, 0.0) + lang_score

                if display_name not in supporting_events:
                    supporting_events[display_name] = []
                supporting_events[display_name].append(e)

                inp = input_text or url_search
                if inp and len(inp) > 2:
                    if display_name not in candidate_queries:
                        candidate_queries[display_name] = []
                    if inp not in candidate_queries[display_name]:
                        candidate_queries[display_name].append(inp)

    if not candidate_scores:
        return {"top_candidate": None, "confidence": "UNKNOWN", "candidates": {}}, []

    sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
    top_candidate, top_score = sorted_candidates[0]

    top_events = supporting_events.get(top_candidate, [])
    top_inputs = candidate_queries.get(top_candidate, [])

    confidence = "LIKELY" if top_score >= 3.0 else "UNKNOWN"

    for inp in top_inputs:
        if "favorite" in inp.lower() or "favourite" in inp.lower() or "my language" in inp.lower():
            confidence = "CONFIRMED"

    summary_data = {
        "top_candidate": top_candidate,
        "score": round(top_score, 1),
        "count": len(top_events),
        "confidence": confidence,
        "queries": top_inputs,
        "all_candidates": {k: round(v, 1) for k, v in sorted_candidates[:5]}
    }

    return summary_data, top_events


def infer_comedian_preference(db: Session) -> Tuple[Dict[str, Any], List[Event]]:
    """
    Scans entire database for comedian & standup signals across titles, inputs, and URLs.
    """
    all_events = db.query(Event).all()

    known_comedians = [
        "Samay Raina", "Ashish Chanchlani", "Aakash Gupta", "Anubhav Singh Bassi",
        "Munawar Faruqui", "Zakir Khan", "Biswa Kalyan Rath", "Kanan Gill",
        "Kenny Sebastian", "Gaurav Kapoor", "Rahul Subramanian", "Harsh Gujral"
    ]

    candidate_counts: Dict[str, int] = {}
    supporting_events: Dict[str, List[Event]] = {}
    candidate_queries: Dict[str, List[str]] = {}

    for e in all_events:
        text_corpus = f"{e.input_text or ''} {extract_url_search_params(e.url) or ''} {e.page_title or ''} {e.content or ''}"
        for comedian in known_comedians:
            if comedian.lower() in text_corpus.lower():
                candidate_counts[comedian] = candidate_counts.get(comedian, 0) + 1
                if comedian not in supporting_events:
                    supporting_events[comedian] = []
                supporting_events[comedian].append(e)

                inp = e.input_text or extract_url_search_params(e.url)
                if inp:
                    if comedian not in candidate_queries: candidate_queries[comedian] = []
                    if inp not in candidate_queries[comedian]: candidate_queries[comedian].append(inp)

    if not candidate_counts:
        return {"top_candidate": None, "confidence": "UNKNOWN", "candidates": {}}, []

    sorted_candidates = sorted(candidate_counts.items(), key=lambda x: x[1], reverse=True)
    top_candidate, top_count = sorted_candidates[0]

    confidence = "LIKELY" if top_count >= 2 else "UNKNOWN"

    summary_data = {
        "top_candidate": top_candidate,
        "count": top_count,
        "confidence": confidence,
        "queries": candidate_queries.get(top_candidate, []),
        "all_candidates": dict(sorted_candidates[:5])
    }

    return summary_data, supporting_events.get(top_candidate, [])


def infer_entertainment_preference(db: Session) -> Tuple[Dict[str, Any], List[Event]]:
    """
    Scans entire database for movie / entertainment title signals.
    """
    all_events = db.query(Event).all()

    media_counts: Dict[str, int] = {}
    supporting_events: Dict[str, List[Event]] = {}

    for e in all_events:
        title = e.page_title or ""
        if "YouTube" in title or "Movie" in title or "Episode" in title or "TMKOC" in title or "Taarak Mehta" in title or "Avengers" in title:
            clean_title = re.sub(r'\(?\d+\)?', '', title).replace('- YouTube', '').strip()
            if len(clean_title) > 5:
                media_counts[clean_title] = media_counts.get(clean_title, 0) + 1
                if clean_title not in supporting_events: supporting_events[clean_title] = []
                supporting_events[clean_title].append(e)

    if not media_counts:
        return {"top_candidate": None, "confidence": "UNKNOWN", "candidates": {}}, []

    sorted_candidates = sorted(media_counts.items(), key=lambda x: x[1], reverse=True)
    top_candidate, top_count = sorted_candidates[0]

    summary_data = {
        "top_candidate": top_candidate,
        "count": top_count,
        "confidence": "LIKELY" if top_count >= 2 else "UNKNOWN",
        "all_candidates": dict(sorted_candidates[:5])
    }

    return summary_data, supporting_events.get(top_candidate, [])


def infer_art_form_preference(db: Session) -> Tuple[Dict[str, Any], List[Event]]:
    """
    Scans entire database to evaluate user engagement across distinct art forms
    (Literature, Music, Film, Theatre, Visual Arts) based on searches, titles, and media events.
    """
    all_events = db.query(Event).all()
    form_scores: Dict[str, float] = {}
    supporting_events: Dict[str, List[Event]] = {}
    candidate_queries: Dict[str, List[str]] = {}

    for e in all_events:
        search_txt = f"{e.input_text or ''} {extract_url_search_params(e.url) or ''}".lower()
        title_txt = (e.page_title or '').lower()

        for form_name, keywords in KNOWN_ART_FORMS:
            matched = False
            for kw in keywords:
                if kw in search_txt or kw in title_txt:
                    matched = True
                    break
            if matched:
                form_scores[form_name] = form_scores.get(form_name, 0.0) + (3.0 if (e.input_text or extract_url_search_params(e.url)) else 1.0)
                if form_name not in supporting_events:
                    supporting_events[form_name] = []
                supporting_events[form_name].append(e)

                inp = e.input_text or extract_url_search_params(e.url)
                if inp:
                    if form_name not in candidate_queries: candidate_queries[form_name] = []
                    if inp not in candidate_queries[form_name]: candidate_queries[form_name].append(inp)

    if not form_scores:
        return {"top_candidate": None, "confidence": "UNKNOWN", "candidates": {}}, []

    sorted_candidates = sorted(form_scores.items(), key=lambda x: x[1], reverse=True)
    top_candidate, top_score = sorted_candidates[0]
    top_events = supporting_events.get(top_candidate, [])

    summary_data = {
        "top_candidate": top_candidate.capitalize(),
        "score": round(top_score, 1),
        "count": len(top_events),
        "confidence": "LIKELY" if top_score >= 3.0 else "UNKNOWN",
        "queries": candidate_queries.get(top_candidate, [])[:6],
        "all_candidates": {k.capitalize(): round(v, 1) for k, v in sorted_candidates}
    }

    return summary_data, top_events


def infer_authors_literature_preference(db: Session) -> Tuple[Dict[str, Any], List[Event]]:
    """
    Discovers authors and literary figures mentioned across search queries, titles, and book pages.
    """
    all_events = db.query(Event).all()
    author_counts: Dict[str, int] = {}
    supporting_events: Dict[str, List[Event]] = {}
    candidate_queries: Dict[str, List[str]] = {}

    potential_figures = [
        "Camus", "Nietzsche", "Osho", "J. Krishnamurti", "Krishnamurti",
        "Carl Sagan", "Sam Harris", "Fyodor Dostoevsky", "Dostoevsky", "Franz Kafka", "Kafka",
        "George Orwell", "Orwell", "Marcus Aurelius", "Haruki Murakami"
    ]

    for e in all_events:
        text = f"{e.input_text or ''} {extract_url_search_params(e.url) or ''} {e.page_title or ''}".lower()
        for fig in potential_figures:
            if fig.lower() in text:
                disp = "J. Krishnamurti" if "krishnamurti" in fig.lower() else ("Albert Camus" if "camus" in fig.lower() else ("Friedrich Nietzsche" if "nietzsche" in fig.lower() else fig))
                author_counts[disp] = author_counts.get(disp, 0) + 1
                if disp not in supporting_events:
                    supporting_events[disp] = []
                supporting_events[disp].append(e)

                inp = e.input_text or extract_url_search_params(e.url)
                if inp:
                    if disp not in candidate_queries: candidate_queries[disp] = []
                    if inp not in candidate_queries[disp]: candidate_queries[disp].append(inp)

    if not author_counts:
        return {"top_candidate": None, "confidence": "UNKNOWN", "candidates": {}}, []

    sorted_candidates = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
    top_candidate, top_count = sorted_candidates[0]
    top_events = supporting_events.get(top_candidate, [])

    summary_data = {
        "top_candidate": top_candidate,
        "count": top_count,
        "confidence": "LIKELY" if top_count >= 1 else "UNKNOWN",
        "queries": candidate_queries.get(top_candidate, []),
        "all_candidates": dict(sorted_candidates[:5])
    }

    return summary_data, top_events


def infer_philosophy_preference(db: Session) -> Tuple[Dict[str, Any], List[Event]]:
    """
    Evaluates philosophical topics, inquiries, and traditions present in user searches.
    """
    all_events = db.query(Event).all()
    trad_counts: Dict[str, int] = {}
    supporting_events: Dict[str, List[Event]] = {}
    candidate_queries: Dict[str, List[str]] = {}

    for e in all_events:
        text = f"{e.input_text or ''} {extract_url_search_params(e.url) or ''} {e.page_title or ''}".lower()
        for trad_name, keywords in KNOWN_PHILOSOPHICAL_TRADITIONS:
            matched = any(kw in text for kw in keywords)
            if matched:
                trad_counts[trad_name] = trad_counts.get(trad_name, 0) + 1
                if trad_name not in supporting_events:
                    supporting_events[trad_name] = []
                supporting_events[trad_name].append(e)

                inp = e.input_text or extract_url_search_params(e.url)
                if inp:
                    if trad_name not in candidate_queries: candidate_queries[trad_name] = []
                    if inp not in candidate_queries[trad_name]: candidate_queries[trad_name].append(inp)

    if not trad_counts:
        return {"top_candidate": None, "confidence": "UNKNOWN", "candidates": {}}, []

    sorted_candidates = sorted(trad_counts.items(), key=lambda x: x[1], reverse=True)
    top_candidate, top_count = sorted_candidates[0]

    summary_data = {
        "top_candidate": top_candidate,
        "count": top_count,
        "confidence": "LIKELY" if top_count >= 2 else "UNKNOWN",
        "queries": candidate_queries.get(top_candidate, [])[:6],
        "all_candidates": dict(sorted_candidates)
    }

    return summary_data, supporting_events.get(top_candidate, [])
