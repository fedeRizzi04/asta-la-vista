"""make strategy tiers global

Revision ID: 91f3c2a7b804
Revises: 4bd995617d1c
Create Date: 2026-08-25 02:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "91f3c2a7b804"
down_revision: str | None = "4bd995617d1c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade():
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("""
            SELECT uuid, strategy_id, role, name, position, color
            FROM tier
            ORDER BY strategy_id, position,
                     CASE role WHEN 'P' THEN 1 WHEN 'D' THEN 2 WHEN 'C' THEN 3 ELSE 4 END,
                     name COLLATE NOCASE
        """)
    ).mappings()

    canonical_by_strategy: dict[str, dict[str, str]] = {}
    global_tiers: dict[str, list[dict[str, object]]] = {}
    duplicate_tiers: list[tuple[str, str]] = []
    for row in rows:
        strategy_id = row["strategy_id"]
        normalized_name = row["name"].strip().casefold()
        canonical = canonical_by_strategy.setdefault(strategy_id, {})
        if normalized_name in canonical:
            duplicate_tiers.append((row["uuid"], canonical[normalized_name]))
            continue
        canonical[normalized_name] = row["uuid"]
        strategy_tiers = global_tiers.setdefault(strategy_id, [])
        strategy_tiers.append(
            {
                "uuid": row["uuid"],
                "strategy_id": strategy_id,
                "name": row["name"],
                "position": len(strategy_tiers),
                "color": row["color"],
            }
        )

    for duplicate_id, canonical_id in duplicate_tiers:
        connection.execute(
            sa.text("UPDATE strategy_entry SET tier_id = :canonical WHERE tier_id = :duplicate"),
            {"canonical": canonical_id, "duplicate": duplicate_id},
        )

    op.create_table(
        "tier_global",
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategy.uuid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("uuid"),
        sa.UniqueConstraint("strategy_id", "name"),
    )
    tier_rows = [tier for tiers in global_tiers.values() for tier in tiers]
    if tier_rows:
        connection.execute(
            sa.text("""
                INSERT INTO tier_global (uuid, strategy_id, name, position, color)
                VALUES (:uuid, :strategy_id, :name, :position, :color)
            """),
            tier_rows,
        )

    _create_strategy_entry_table("strategy_entry_global", "tier_global")
    connection.execute(
        sa.text("""
            INSERT INTO strategy_entry_global
                (uuid, strategy_id, player_id, role, tier_id, note)
            SELECT uuid, strategy_id, player_id, role, tier_id, note
            FROM strategy_entry
        """)
    )
    op.drop_table("strategy_entry")
    op.drop_table("tier")
    op.rename_table("tier_global", "tier")
    op.rename_table("strategy_entry_global", "strategy_entry")


def downgrade():
    connection = op.get_bind()
    role_type = sa.Enum("P", "D", "C", "A", name="role", native_enum=False)
    op.create_table(
        "tier_legacy",
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("role", role_type, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategy.uuid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("uuid"),
        sa.UniqueConstraint("strategy_id", "role", "name"),
        sa.UniqueConstraint("strategy_id", "role", "position"),
    )
    connection.execute(
        sa.text("""
            INSERT INTO tier_legacy (uuid, strategy_id, role, name, position, color)
            SELECT uuid, strategy_id, 'P', name, position, color FROM tier
        """)
    )
    _create_strategy_entry_table("strategy_entry_legacy", "tier_legacy")
    connection.execute(
        sa.text("""
            INSERT INTO strategy_entry_legacy
                (uuid, strategy_id, player_id, role, tier_id, note)
            SELECT uuid, strategy_id, player_id, role, tier_id, note
            FROM strategy_entry
        """)
    )
    op.drop_table("strategy_entry")
    op.drop_table("tier")
    op.rename_table("tier_legacy", "tier")
    op.rename_table("strategy_entry_legacy", "strategy_entry")


def _create_strategy_entry_table(table_name: str, tier_table_name: str) -> None:
    role_type = sa.Enum("P", "D", "C", "A", name="role", native_enum=False)
    op.create_table(
        table_name,
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), nullable=False),
        sa.Column("player_id", sa.String(length=32), nullable=False),
        sa.Column("role", role_type, nullable=False),
        sa.Column("tier_id", sa.String(length=36), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["player.external_id"]),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategy.uuid"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tier_id"], [f"{tier_table_name}.uuid"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("uuid"),
        sa.UniqueConstraint("strategy_id", "player_id"),
    )
