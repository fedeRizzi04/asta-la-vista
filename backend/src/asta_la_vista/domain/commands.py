from dataclasses import dataclass


class Command:
    """Base class for application commands."""


@dataclass(frozen=True)
class PlayerRow:
    external_id: str
    name: str
    team: str
    role: str
    quotation: int | None = None
    # ``None`` means that the source file has no RM column. It differs from an
    # empty tuple, which is an explicit empty RM value.
    mantra_roles: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ImportPlayers(Command):
    players: tuple[PlayerRow, ...]
    allow_live_auction: bool = False


@dataclass(frozen=True)
class CreateAuction(Command):
    name: str
    initial_credits: int
    goalkeeper_slots: int
    defender_slots: int
    midfielder_slots: int
    forward_slots: int
    participant_names: tuple[str, ...]
    strategy_id: str | None = None


@dataclass(frozen=True)
class StartAuction(Command):
    auction_id: str


@dataclass(frozen=True)
class RecordPurchase(Command):
    auction_id: str
    player_id: str
    participant_id: str
    price: int


@dataclass(frozen=True)
class AmendPurchase(Command):
    auction_id: str
    purchase_id: str
    participant_id: str
    price: int


@dataclass(frozen=True)
class CancelPurchase(Command):
    auction_id: str
    purchase_id: str


@dataclass(frozen=True)
class CompleteAuction(Command):
    auction_id: str


@dataclass(frozen=True)
class ReopenAuction(Command):
    auction_id: str


@dataclass(frozen=True)
class DeleteAuction(Command):
    auction_id: str


@dataclass(frozen=True)
class SetAuctionStrategy(Command):
    auction_id: str
    strategy_id: str | None


@dataclass(frozen=True)
class CreateStrategy(Command):
    name: str


@dataclass(frozen=True)
class RenameStrategy(Command):
    strategy_id: str
    name: str


@dataclass(frozen=True)
class DeleteStrategy(Command):
    strategy_id: str


@dataclass(frozen=True)
class AddTier(Command):
    strategy_id: str
    name: str
    color: str | None = None


@dataclass(frozen=True)
class UpdateTier(Command):
    strategy_id: str
    tier_id: str
    name: str
    color: str | None = None


@dataclass(frozen=True)
class RemoveTier(Command):
    strategy_id: str
    tier_id: str


@dataclass(frozen=True)
class ReorderTiers(Command):
    strategy_id: str
    tier_ids: tuple[str, ...]


@dataclass(frozen=True)
class UpdateStrategyPlayer(Command):
    strategy_id: str
    player_id: str
    tier_id: str | None
    note: str
    maximum_price_percentage: float | None


@dataclass(frozen=True)
class DuplicateStrategy(Command):
    strategy_id: str
    name: str


@dataclass(frozen=True)
class TierImportRow:
    name: str
    # Empty string means the source row has no tier for this player (note-only row).
    fascia: str = ""
    note: str = ""
    maximum_price_percentage: float | None = None
    # Colour of the tier named in `fascia`; empty when the source has none.
    colore: str = ""


@dataclass(frozen=True)
class ImportStrategy(Command):
    name: str
    rows: tuple[TierImportRow, ...]
    allow_unmatched_players: bool = False
