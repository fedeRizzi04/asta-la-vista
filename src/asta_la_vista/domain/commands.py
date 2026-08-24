from dataclasses import dataclass


class Command:
    """Base class for application commands."""


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
class CreateStrategy(Command):
    name: str


@dataclass(frozen=True)
class AddTier(Command):
    strategy_id: str
    role: str
    name: str
    color: str | None = None


@dataclass(frozen=True)
class AssignPlayerToTier(Command):
    strategy_id: str
    player_id: str
    tier_id: str


@dataclass(frozen=True)
class SetStrategyPlayerNote(Command):
    strategy_id: str
    player_id: str
    note: str


@dataclass(frozen=True)
class DuplicateStrategy(Command):
    strategy_id: str
    name: str
