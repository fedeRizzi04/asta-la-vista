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


@dataclass(frozen=True)
class StartAuction(Command):
    auction_id: str


@dataclass(frozen=True)
class RecordPurchase(Command):
    auction_id: str
    player_id: str
    player_name: str
    role: str
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
