from sqlalchemy import inspect
from models.sessions import BrowserSession


def test_session_model_structure():
    """
    Structurally verify the BrowserSession model fields match Task 3.1 requirements.
    This avoids relying on a live database connection which is currently blocked.
    """
    mapper = inspect(BrowserSession)

    # Extract columns
    columns = {col.name: col for col in mapper.columns}

    # Verify exact required fields
    assert "id" in columns
    assert "user_id" in columns
    assert "start_time" in columns
    assert "end_time" in columns
    assert "event_count" in columns
    assert "created_at" in columns
    assert "updated_at" in columns

    # Verify primary key
    assert columns["id"].primary_key is True

    # Verify indexes for performance
    assert columns["user_id"].index is True
    assert columns["start_time"].index is True

    # Verify nullability
    assert columns["start_time"].nullable is False
    assert columns["end_time"].nullable is False
    assert columns["event_count"].nullable is False
