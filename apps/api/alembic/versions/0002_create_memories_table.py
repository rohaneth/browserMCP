"""create_memories_table

Revision ID: 0002_create_memories_table
Revises: 0001_create_events_table
Create Date: 2026-08-18 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = "0002_create_memories_table"
down_revision: Union[str, None] = "0001_create_events_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Create memories table
    op.create_table(
        "memories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(384), nullable=True),
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
        sa.Column("embedding_model_version", sa.String(length=50), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. Create memory_evidence table
    op.create_table(
        "memory_evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("memory_id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["memory_id"], ["memories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_memory_evidence_event_id"),
        "memory_evidence",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_evidence_memory_id"),
        "memory_evidence",
        ["memory_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_memory_evidence_memory_id"), table_name="memory_evidence")
    op.drop_index(op.f("ix_memory_evidence_event_id"), table_name="memory_evidence")
    op.drop_table("memory_evidence")
    op.drop_table("memories")
    op.execute("DROP EXTENSION IF EXISTS vector")
