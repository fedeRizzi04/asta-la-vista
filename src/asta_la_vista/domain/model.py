from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from asta_la_vista.domain import events
from asta_la_vista.exceptions import NotFoundError, ValidationError


def new_uuid() -> str:
    return str(uuid4())


class Role(StrEnum):
    GOALKEEPER = "P"
    DEFENDER = "D"
    MIDFIELDER = "C"
    FORWARD = "A"


class AuctionStatus(StrEnum):
    DRAFT = "draft"
    LIVE = "live"
    COMPLETED = "completed"


@dataclass(frozen=True)
class RosterSlots:
    goalkeepers: int
    defenders: int
    midfielders: int
    forwards: int

    def __post_init__(self):
        if any(value < 0 for value in self.as_dict().values()):
            raise ValidationError("Roster slots cannot be negative")
        if self.total == 0:
            raise ValidationError("A roster must contain at least one slot")

    def for_role(self, role: Role) -> int:
        return self.as_dict()[role]

    def as_dict(self) -> dict[Role, int]:
        return {
            Role.GOALKEEPER: self.goalkeepers,
            Role.DEFENDER: self.defenders,
            Role.MIDFIELDER: self.midfielders,
            Role.FORWARD: self.forwards,
        }

    @property
    def total(self) -> int:
        return sum(self.as_dict().values())


@dataclass
class Participant:
    name: str
    uuid: str


@dataclass
class Purchase:
    player_id: str
    player_name: str
    role: Role
    participant_id: str
    price: int
    uuid: str
    cancelled: bool = False


class Auction:
    minimum_price = 1

    def __init__(
        self,
        name: str,
        initial_credits: int,
        slots: RosterSlots,
        uuid: str | None = None,
    ):
        name = name.strip()
        if not name:
            raise ValidationError("Auction name is required")
        if initial_credits < slots.total * self.minimum_price:
            raise ValidationError("Initial credits cannot cover the roster")
        self.uuid = uuid or new_uuid()
        self.name = name
        self.initial_credits = initial_credits
        self.slots = slots
        self.status = AuctionStatus.DRAFT
        self.participants: list[Participant] = []
        self.purchases: list[Purchase] = []
        self.events: deque[events.Event] = deque()

    def add_participant(self, name: str, uuid: str | None = None) -> str:
        self._require_status(AuctionStatus.DRAFT)
        name = name.strip()
        if not name:
            raise ValidationError("Participant name is required")
        if any(participant.name.casefold() == name.casefold() for participant in self.participants):
            raise ValidationError("Participant names must be unique")
        participant = Participant(name, uuid or new_uuid())
        self.participants.append(participant)
        return participant.uuid

    def start(self):
        self._require_status(AuctionStatus.DRAFT)
        if not self.participants:
            raise ValidationError("An auction needs at least one participant")
        self.status = AuctionStatus.LIVE
        self.events.append(events.AuctionStarted(self.uuid))

    def complete(self):
        self._require_status(AuctionStatus.LIVE)
        self.status = AuctionStatus.COMPLETED
        self.events.append(events.AuctionCompleted(self.uuid))

    def reopen(self):
        self._require_status(AuctionStatus.COMPLETED)
        self.status = AuctionStatus.LIVE
        self.events.append(events.AuctionReopened(self.uuid))

    def record_purchase(
        self,
        player_id: str,
        player_name: str,
        role: Role,
        participant_id: str,
        price: int,
        uuid: str | None = None,
    ) -> str:
        self._require_status(AuctionStatus.LIVE)
        self._participant(participant_id)
        if any(p.player_id == player_id for p in self._active_purchases()):
            raise ValidationError("Player is already purchased")
        self._validate_purchase(participant_id, role, price)
        purchase = Purchase(
            player_id=player_id,
            player_name=player_name,
            role=role,
            participant_id=participant_id,
            price=price,
            uuid=uuid or new_uuid(),
        )
        self.purchases.append(purchase)
        self.events.append(events.PurchaseRecorded(self.uuid, purchase.uuid))
        return purchase.uuid

    def amend_purchase(self, purchase_id: str, participant_id: str, price: int):
        self._require_status(AuctionStatus.LIVE)
        purchase = self._purchase(purchase_id)
        self._participant(participant_id)
        excluded = {purchase.uuid}
        self._validate_purchase(participant_id, purchase.role, price, excluded)
        previous_participant_id, previous_price = purchase.participant_id, purchase.price
        purchase.participant_id = participant_id
        purchase.price = price
        self.events.append(
            events.PurchaseAmended(
                self.uuid, purchase.uuid, previous_participant_id, previous_price
            )
        )

    def cancel_purchase(self, purchase_id: str):
        self._require_status(AuctionStatus.LIVE)
        purchase = self._purchase(purchase_id)
        purchase.cancelled = True
        self.events.append(events.PurchaseCancelled(self.uuid, purchase.uuid))

    def remaining_credits(self, participant_id: str) -> int:
        self._participant(participant_id)
        spent = sum(p.price for p in self._active_purchases() if p.participant_id == participant_id)
        return self.initial_credits - spent

    def filled_slots(self, participant_id: str, role: Role) -> int:
        self._participant(participant_id)
        return sum(
            p.role == role for p in self._active_purchases() if p.participant_id == participant_id
        )

    def remaining_slots(self, participant_id: str) -> int:
        self._participant(participant_id)
        filled = sum(p.participant_id == participant_id for p in self._active_purchases())
        return self.slots.total - filled

    def maximum_bid(self, participant_id: str) -> int:
        remaining_slots = self.remaining_slots(participant_id)
        if remaining_slots == 0:
            return 0
        return self.remaining_credits(participant_id) - (remaining_slots - 1) * self.minimum_price

    def _validate_purchase(
        self,
        participant_id: str,
        role: Role,
        price: int,
        excluded_purchase_ids: set[str] | None = None,
    ):
        if isinstance(price, bool) or not isinstance(price, int) or price < self.minimum_price:
            raise ValidationError("Price must be a positive integer")
        purchases = self._active_purchases(excluded_purchase_ids)
        role_count = sum(p.role == role and p.participant_id == participant_id for p in purchases)
        if role_count >= self.slots.for_role(role):
            raise ValidationError("No slot is available for this role")
        spent = sum(p.price for p in purchases if p.participant_id == participant_id)
        filled = sum(p.participant_id == participant_id for p in purchases)
        remaining_credits = self.initial_credits - spent
        remaining_slots = self.slots.total - filled
        maximum_bid = remaining_credits - (remaining_slots - 1) * self.minimum_price
        if price > maximum_bid:
            raise ValidationError("Price exceeds the participant maximum bid")

    def _active_purchases(self, excluded_purchase_ids: set[str] | None = None) -> list[Purchase]:
        excluded_purchase_ids = excluded_purchase_ids or set()
        return [
            p for p in self.purchases if not p.cancelled and p.uuid not in excluded_purchase_ids
        ]

    def _participant(self, participant_id: str) -> Participant:
        participant = next((p for p in self.participants if p.uuid == participant_id), None)
        if participant is None:
            raise NotFoundError("Participant not found")
        return participant

    def _purchase(self, purchase_id: str) -> Purchase:
        purchase = next(
            (p for p in self.purchases if p.uuid == purchase_id and not p.cancelled), None
        )
        if purchase is None:
            raise NotFoundError("Purchase not found")
        return purchase

    def _require_status(self, expected: AuctionStatus):
        if self.status != expected:
            raise ValidationError(f"Auction must be {expected.value}")
