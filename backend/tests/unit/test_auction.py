import pytest

from asta_la_vista.domain.model import Auction, AuctionStatus, Role, RosterSlots
from asta_la_vista.exceptions import NotFoundError, ValidationError


@pytest.fixture
def auction() -> Auction:
    auction = Auction("Friends league", 100, RosterSlots(1, 2, 2, 1), uuid="auction-1")
    auction.add_participant("Alice", uuid="alice")
    auction.add_participant("Bob", uuid="bob")
    auction.start()
    return auction


def test_purchase_updates_credits_slots_and_maximum_bid(auction: Auction):
    auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "alice", 20)

    assert auction.remaining_credits("alice") == 80
    assert auction.filled_slots("alice", Role.GOALKEEPER) == 1
    assert auction.remaining_slots("alice") == 5
    assert auction.maximum_bid("alice") == 76


def test_purchase_must_preserve_one_credit_for_every_later_slot(auction: Auction):
    with pytest.raises(ValidationError):
        auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "alice", 96)

    auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "alice", 95)
    assert auction.maximum_bid("alice") == 1


def test_player_and_role_slots_cannot_be_purchased_twice(auction: Auction):
    auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "alice", 10)

    with pytest.raises(ValidationError):
        auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "bob", 10)
    with pytest.raises(ValidationError):
        auction.record_purchase("player-2", "Other goalkeeper", Role.GOALKEEPER, "alice", 10)


def test_purchase_can_change_winner_and_price(auction: Auction):
    purchase_id = auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "alice", 20)

    auction.amend_purchase(purchase_id, "bob", 30)

    assert auction.remaining_credits("alice") == 100
    assert auction.remaining_credits("bob") == 70
    assert auction.filled_slots("alice", Role.GOALKEEPER) == 0
    assert auction.filled_slots("bob", Role.GOALKEEPER) == 1


def test_cancelled_purchase_restores_budget_slot_and_player_availability(auction: Auction):
    purchase_id = auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "alice", 20)

    auction.cancel_purchase(purchase_id)
    replacement_id = auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "bob", 25)

    assert replacement_id != purchase_id
    assert auction.remaining_credits("alice") == 100
    assert auction.filled_slots("alice", Role.GOALKEEPER) == 0
    with pytest.raises(NotFoundError):
        auction.cancel_purchase(purchase_id)


def test_completed_auction_can_only_change_after_reopening(auction: Auction):
    auction.complete()
    assert auction.status == AuctionStatus.COMPLETED

    with pytest.raises(ValidationError):
        auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "alice", 20)

    auction.reopen()
    auction.record_purchase("player-1", "Goalkeeper", Role.GOALKEEPER, "alice", 20)
    assert auction.status == AuctionStatus.LIVE
