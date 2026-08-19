from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from models.events import Event


def test_event_model_table_creation_sql():
    # Statically verify that the model produces valid CREATE TABLE DDL
    create_stmt = CreateTable(Event.__table__).compile(dialect=postgresql.dialect())
    sql = str(create_stmt)

    assert "events" in sql
    assert "event_id" in sql
    assert "timestamp" in sql
    assert "event_type" in sql
    assert "canonical_url" in sql
    assert "JSONB" in sql or "jsonb" in sql.lower()


def test_migration_file_exists():
    import os

    migration_dir = os.path.join(os.path.dirname(__file__), "..", "alembic", "versions")
    files = [
        f
        for f in os.listdir(migration_dir)
        if f.endswith(".py") and "create_events" in f
    ]
    assert len(files) == 1, "Migration file for events table must exist"
