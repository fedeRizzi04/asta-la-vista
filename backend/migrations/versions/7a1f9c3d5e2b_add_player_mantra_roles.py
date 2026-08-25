"""add player mantra roles

Revision ID: 7a1f9c3d5e2b
Revises: 311384b86c14
Create Date: 2026-08-25 09:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7a1f9c3d5e2b"
down_revision: str | None = "311384b86c14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    op.add_column("player", sa.Column("mantra_roles", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("player", "mantra_roles")
