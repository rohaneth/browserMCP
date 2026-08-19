"""create collection settings table

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-18 15:50:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "collection_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("is_paused", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Initialize the singleton settings row
    op.execute("INSERT INTO collection_settings (id, is_paused) VALUES (1, false)")


def downgrade() -> None:
    op.drop_table("collection_settings")
