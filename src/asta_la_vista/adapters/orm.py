from collections import deque

import sqlalchemy as sa
from sqlalchemy.orm import composite, registry, relationship

from asta_la_vista.domain import model

mapper_registry = registry()
metadata = mapper_registry.metadata

role_type = sa.Enum(
    model.Role,
    values_callable=lambda roles: [role.value for role in roles],
    native_enum=False,
    length=1,
)
auction_status_type = sa.Enum(
    model.AuctionStatus,
    values_callable=lambda statuses: [status.value for status in statuses],
    native_enum=False,
    length=10,
)

players = sa.Table(
    "player",
    metadata,
    sa.Column("external_id", sa.String(32), primary_key=True),
    sa.Column("name", sa.String(120), nullable=False),
    sa.Column("team", sa.String(80), nullable=False),
    sa.Column("role", role_type, nullable=False),
    sa.Column("active", sa.Boolean, nullable=False),
)

strategies = sa.Table(
    "strategy",
    metadata,
    sa.Column("uuid", sa.String(36), primary_key=True),
    sa.Column("name", sa.String(120), nullable=False, unique=True),
)

tiers = sa.Table(
    "tier",
    metadata,
    sa.Column("uuid", sa.String(36), primary_key=True),
    sa.Column("strategy_id", sa.ForeignKey("strategy.uuid", ondelete="CASCADE"), nullable=False),
    sa.Column("role", role_type, nullable=False),
    sa.Column("name", sa.String(80), nullable=False),
    sa.Column("position", sa.Integer, nullable=False),
    sa.Column("color", sa.String(32)),
    sa.UniqueConstraint("strategy_id", "role", "name"),
    sa.UniqueConstraint("strategy_id", "role", "position"),
)

strategy_entries = sa.Table(
    "strategy_entry",
    metadata,
    sa.Column("uuid", sa.String(36), primary_key=True),
    sa.Column("strategy_id", sa.ForeignKey("strategy.uuid", ondelete="CASCADE"), nullable=False),
    sa.Column("player_id", sa.ForeignKey("player.external_id"), nullable=False),
    sa.Column("role", role_type, nullable=False),
    sa.Column("tier_id", sa.ForeignKey("tier.uuid", ondelete="SET NULL")),
    sa.Column("note", sa.Text, nullable=False),
    sa.UniqueConstraint("strategy_id", "player_id"),
)

auctions = sa.Table(
    "auction",
    metadata,
    sa.Column("uuid", sa.String(36), primary_key=True),
    sa.Column("name", sa.String(120), nullable=False),
    sa.Column("initial_credits", sa.Integer, nullable=False),
    sa.Column("goalkeeper_slots", sa.Integer, nullable=False),
    sa.Column("defender_slots", sa.Integer, nullable=False),
    sa.Column("midfielder_slots", sa.Integer, nullable=False),
    sa.Column("forward_slots", sa.Integer, nullable=False),
    sa.Column("strategy_id", sa.ForeignKey("strategy.uuid", ondelete="SET NULL")),
    sa.Column("status", auction_status_type, nullable=False),
)

participants = sa.Table(
    "participant",
    metadata,
    sa.Column("uuid", sa.String(36), primary_key=True),
    sa.Column("auction_id", sa.ForeignKey("auction.uuid", ondelete="CASCADE"), nullable=False),
    sa.Column("name", sa.String(120), nullable=False),
    sa.UniqueConstraint("auction_id", "name"),
)

purchases = sa.Table(
    "purchase",
    metadata,
    sa.Column("uuid", sa.String(36), primary_key=True),
    sa.Column("auction_id", sa.ForeignKey("auction.uuid", ondelete="CASCADE"), nullable=False),
    sa.Column("player_id", sa.ForeignKey("player.external_id"), nullable=False),
    sa.Column("player_name", sa.String(120), nullable=False),
    sa.Column("role", role_type, nullable=False),
    sa.Column("participant_id", sa.ForeignKey("participant.uuid"), nullable=False),
    sa.Column("price", sa.Integer, nullable=False),
    sa.Column("cancelled", sa.Boolean, nullable=False),
    sa.CheckConstraint("price >= 1"),
)
sa.Index(
    "uq_active_purchase_player",
    purchases.c.auction_id,
    purchases.c.player_id,
    unique=True,
    sqlite_where=purchases.c.cancelled.is_(False),
)


def start_mappers():
    if sa.inspect(model.Player, raiseerr=False) is not None:
        return
    mapper_registry.map_imperatively(model.Player, players)
    mapper_registry.map_imperatively(model.Tier, tiers)
    mapper_registry.map_imperatively(
        model.StrategyEntry,
        strategy_entries,
        properties={"_tier": relationship(model.Tier, foreign_keys=[strategy_entries.c.tier_id])},
    )
    mapper_registry.map_imperatively(
        model.Strategy,
        strategies,
        properties={
            "tiers": relationship(model.Tier, cascade="all, delete-orphan"),
            "entries": relationship(model.StrategyEntry, cascade="all, delete-orphan"),
        },
    )
    mapper_registry.map_imperatively(model.Participant, participants)
    mapper_registry.map_imperatively(model.Purchase, purchases)
    mapper_registry.map_imperatively(
        model.Auction,
        auctions,
        properties={
            "slots": composite(
                model.RosterSlots,
                auctions.c.goalkeeper_slots,
                auctions.c.defender_slots,
                auctions.c.midfielder_slots,
                auctions.c.forward_slots,
            ),
            "participants": relationship(model.Participant, cascade="all, delete-orphan"),
            "purchases": relationship(model.Purchase, cascade="all, delete-orphan"),
        },
    )
    for aggregate in (model.Player, model.Strategy, model.Auction):
        sa.event.listen(aggregate, "load", _restore_events)


def _restore_events(target, _context):
    target.events = deque()
