"""add player quotation

Revision ID: cc0c61733f8f
Revises: 16fc5d0fe168
Create Date: 2026-08-25 04:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cc0c61733f8f"
down_revision: str | None = "16fc5d0fe168"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    op.add_column(
        "player",
        sa.Column(
            "quotation",
            sa.Integer(),
            sa.CheckConstraint("quotation >= 0", name="ck_player_quotation"),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("player", "quotation")
