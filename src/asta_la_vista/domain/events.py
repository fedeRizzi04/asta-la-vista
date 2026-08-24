from dataclasses import dataclass


class Event:
    """Base class for domain events."""


@dataclass(frozen=True)
class AuctionStarted(Event):
    auction_id: str


@dataclass(frozen=True)
class PurchaseRecorded(Event):
    auction_id: str
    purchase_id: str


@dataclass(frozen=True)
class PurchaseAmended(Event):
    auction_id: str
    purchase_id: str
    previous_participant_id: str
    previous_price: int


@dataclass(frozen=True)
class PurchaseCancelled(Event):
    auction_id: str
    purchase_id: str


@dataclass(frozen=True)
class AuctionCompleted(Event):
    auction_id: str


@dataclass(frozen=True)
class AuctionReopened(Event):
    auction_id: str
