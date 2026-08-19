import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.session import SessionLocal
from services.investigation import run_investigation


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_programming_language_preference(db):
    inv, evs = run_investigation(db, "What is my favourite programming language?")
    assert inv.status == "completed"
    assert len(evs) > 0
    assert "Java" in inv.summary


def test_movie_preference(db):
    inv, evs = run_investigation(db, "What is my favourite movie?")
    assert inv.status == "completed"
    assert len(evs) > 0
    assert "Avengers" in inv.summary or "Endgame" in inv.summary


def test_art_form_preference(db):
    inv, evs = run_investigation(db, "Which art form do I like?")
    assert inv.status == "completed"
    assert len(evs) > 0
    assert "Film" in inv.summary


def test_general_inference_introvert_vs_extrovert(db):
    inv, evs = run_investigation(db, "Am I introvert or extrovert based on my browsing?")
    assert inv.status == "completed"
    assert len(evs) > 0
    assert "Introvert" in inv.summary or "BEHAVIORAL INFERENCE" in inv.summary


def test_entity_fact_check_dostoevsky_not_found(db):
    inv, evs = run_investigation(db, "Did I search Dostoevsky?")
    assert inv.status == "completed"
    assert len(evs) == 0
    assert "NOT FOUND / UNAVAILABLE" in inv.summary


def test_entity_fact_check_avengers_endgame(db):
    inv, evs = run_investigation(db, "Did I watch Avengers Endgame?")
    assert inv.status == "completed"
    assert len(evs) >= 1
    assert "CONFIRMED" in inv.summary


def test_open_ended_what_have_you_learned(db):
    inv, evs = run_investigation(db, "What have you learned about me from my browsing that I probably haven't noticed?")
    assert inv.status == "completed"
    assert len(evs) > 0
    assert "INFERRED" in inv.summary or "PATTERNS" in inv.summary or "BEHAVIORAL" in inv.summary


def test_open_ended_what_do_i_enjoy(db):
    inv, evs = run_investigation(db, "What do I seem to enjoy?")
    assert inv.status == "completed"
    assert len(evs) > 0


def test_open_ended_topics_interested(db):
    inv, evs = run_investigation(db, "What topics am I most interested in?")
    assert inv.status == "completed"
    assert len(evs) > 0


def test_open_ended_entertainment_preference(db):
    inv, evs = run_investigation(db, "What kind of entertainment do I prefer?")
    assert inv.status == "completed"
    assert len(evs) > 0


def test_temporal_yesterday(db):
    inv, evs = run_investigation(db, "What did I search about yesterday?")
    assert inv.status == "completed"


def test_fuzzy_avanger_endgame(db):
    inv, evs = run_investigation(db, "avanger endgame")
    assert inv.status == "completed"
    assert len(evs) >= 1


def test_natural_language_wording_variations(db):
    inv, evs = run_investigation(db, "tell me which coding language i use the most")
    assert inv.status == "completed"
    assert len(evs) > 0
    assert "Java" in inv.summary
