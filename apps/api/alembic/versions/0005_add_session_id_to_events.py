"""add session_id to events

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-18 16:08:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events", sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_index(
        op.f("ix_events_session_id"), "events", ["session_id"], unique=False
    )
    op.create_foreign_key(
        "fk_events_session_id",
        "events",
        "sessions",
        ["session_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_events_session_id", "events", type_="foreignkey")
    op.drop_index(op.f("ix_events_session_id"), table_name="events")
    op.drop_column("events", "session_id")
