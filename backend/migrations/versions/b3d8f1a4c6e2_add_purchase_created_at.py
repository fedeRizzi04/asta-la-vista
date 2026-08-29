"""add purchase created_at

Revision ID: b3d8f1a4c6e2
Revises: 7a1f9c3d5e2b
Create Date: 2026-08-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3d8f1a4c6e2"
down_revision: str | None = "7a1f9c3d5e2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    with op.batch_alter_table("purchase") as batch_op:
        batch_op.add_column(
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now())
        )


def downgrade():
    with op.batch_alter_table("purchase") as batch_op:
        batch_op.drop_column("created_at")
