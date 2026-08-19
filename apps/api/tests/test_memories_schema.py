from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from models.memories import Memory, MemoryEvidence


def test_memory_table_schema():
    """
    Test that the Memory table compiles correctly to PostgreSQL syntax
    and contains the necessary columns, including the vector embedding column.
    """
    create_stmt = str(
        CreateTable(Memory.__table__).compile(dialect=postgresql.dialect())
    )

    # Check core table creation
    assert "CREATE TABLE memories" in create_stmt
    assert "id UUID NOT NULL" in create_stmt

    # Check vector dimension
    assert "embedding VECTOR(384)" in create_stmt

    # Check metadata tracking model provenance
    assert "embedding_model VARCHAR(100)" in create_stmt
    assert "embedding_model_version VARCHAR(50)" in create_stmt
    assert "type VARCHAR(50) NOT NULL" in create_stmt


def test_memory_evidence_table_schema():
    """
    Test that the MemoryEvidence junction table establishes proper foreign keys.
    """
    create_stmt = str(
        CreateTable(MemoryEvidence.__table__).compile(dialect=postgresql.dialect())
    )

    assert "CREATE TABLE memory_evidence" in create_stmt
    assert "memory_id UUID NOT NULL" in create_stmt
    assert "event_id UUID NOT NULL" in create_stmt

    # Verify foreign key constraints pointing to memory and event UUIDs
    assert "FOREIGN KEY(memory_id) REFERENCES memories (id)" in create_stmt
    assert "FOREIGN KEY(event_id) REFERENCES events (event_id)" in create_stmt
