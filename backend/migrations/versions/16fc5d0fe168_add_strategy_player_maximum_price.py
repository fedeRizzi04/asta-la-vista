"""add strategy player maximum price

Revision ID: 16fc5d0fe168
Revises: 91f3c2a7b804
Create Date: 2026-08-25 03:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "16fc5d0fe168"
down_revision: str | None = "91f3c2a7b804"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    with op.batch_alter_table("strategy_entry") as batch_op:
        batch_op.add_column(sa.Column("maximum_price", sa.Integer(), nullable=True))
        batch_op.create_check_constraint(
            "ck_strategy_entry_maximum_price",
            "maximum_price IS NULL OR maximum_price >= 1",
        )


def downgrade():
    with op.batch_alter_table("strategy_entry") as batch_op:
        batch_op.drop_constraint("ck_strategy_entry_maximum_price", type_="check")
        batch_op.drop_column("maximum_price")
