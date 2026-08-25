"""convert strategy player price to percentage

Revision ID: 311384b86c14
Revises: cc0c61733f8f
Create Date: 2026-08-25 04:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "311384b86c14"
down_revision: str | None = "cc0c61733f8f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    with op.batch_alter_table("strategy_entry") as batch_op:
        batch_op.drop_constraint("ck_strategy_entry_maximum_price", type_="check")
        batch_op.drop_column("maximum_price")
        batch_op.add_column(sa.Column("maximum_price_percentage", sa.Numeric(4, 1), nullable=True))
        batch_op.create_check_constraint(
            "ck_strategy_entry_maximum_price_percentage",
            "maximum_price_percentage IS NULL"
            " OR (maximum_price_percentage > 0 AND maximum_price_percentage <= 100)",
        )


def downgrade():
    with op.batch_alter_table("strategy_entry") as batch_op:
        batch_op.drop_constraint("ck_strategy_entry_maximum_price_percentage", type_="check")
        batch_op.drop_column("maximum_price_percentage")
        batch_op.add_column(sa.Column("maximum_price", sa.Integer(), nullable=True))
        batch_op.create_check_constraint(
            "ck_strategy_entry_maximum_price",
            "maximum_price IS NULL OR maximum_price >= 1",
        )
