import pytest
from sqlalchemy.exc import IntegrityError

from asta_la_vista.adapters import orm, repository
from asta_la_vista.domain.model import Auction, Player, Role, RosterSlots, Strategy


def test_auction_round_trip_keeps_rosters_and_purchase_role(session_factory):
    with session_factory() as session:
        player = Player("5841", "Svilar", "Roma", Role.GOALKEEPER)
        auction = Auction("Friends league", 100, RosterSlots(1, 2, 2, 1), uuid="auction-1")
        participant_id = auction.add_participant("Alice", uuid="alice")
        auction.start()
        auction.record_purchase(
            player.external_id,
            player.name,
            player.role,
            participant_id,
            20,
            uuid="purchase-1",
        )
        session.add(player)
        repository.AuctionRepository(session).add(auction)
        session.commit()

    with session_factory() as session:
        saved = repository.AuctionRepository(session).get("auction-1")

        assert saved is not None
        assert saved.slots == RosterSlots(1, 2, 2, 1)
        assert saved.purchases[0].role == Role.GOALKEEPER
        assert saved.remaining_credits("alice") == 80
        assert saved.maximum_bid("alice") == 76
        assert list(saved.events) == []


def test_strategy_round_trip_keeps_tiers_assignments_and_notes(session_factory):
    with session_factory() as session:
        player = Player("2764", "Martinez L.", "Inter", Role.FORWARD)
        strategy = Strategy("Main strategy", uuid="strategy-1")
        tier_id = strategy.add_tier(Role.FORWARD, "Top", "#ef4444", uuid="tier-1")
        strategy.assign_player(player.external_id, player.role, tier_id)
        strategy.set_player_note(player.external_id, player.role, "Primary target")
        session.add(player)
        repository.StrategyRepository(session).add(strategy)
        session.commit()

    with session_factory() as session:
        saved = repository.StrategyRepository(session).get("strategy-1")

        assert saved is not None
        assert [(tier.role, tier.name, tier.position) for tier in saved.tiers] == [
            (Role.FORWARD, "Top", 0)
        ]
        assert saved.entries[0].player_id == "2764"
        assert saved.entries[0].note == "Primary target"
        assert list(saved.events) == []


def test_strategy_repository_finds_every_strategy_containing_a_player(session_factory):
    with session_factory() as session:
        player = Player("2764", "Martinez L.", "Inter", Role.FORWARD)
        first = Strategy("First", uuid="strategy-1")
        second = Strategy("Second", uuid="strategy-2")
        first.set_player_note(player.external_id, player.role, "Target")
        second.set_player_note(player.external_id, player.role, "Alternative")
        session.add(player)
        session.add_all([first, second])
        session.commit()

    with session_factory() as session:
        saved = repository.StrategyRepository(session).list_containing_player("2764")

        assert {strategy.uuid for strategy in saved} == {"strategy-1", "strategy-2"}


def test_database_rejects_two_active_purchases_of_the_same_player(session_factory):
    with session_factory() as session:
        player = Player("5841", "Svilar", "Roma", Role.GOALKEEPER)
        auction = Auction("Friends league", 100, RosterSlots(1, 2, 2, 1), uuid="auction-1")
        participant_id = auction.add_participant("Alice", uuid="alice")
        auction.start()
        auction.record_purchase(
            player.external_id,
            player.name,
            player.role,
            participant_id,
            20,
            uuid="purchase-1",
        )
        session.add_all([player, auction])
        session.commit()

        with pytest.raises(IntegrityError):
            session.execute(
                orm.purchases.insert().values(
                    uuid="purchase-2",
                    auction_id=auction.uuid,
                    player_id=player.external_id,
                    player_name=player.name,
                    role=player.role,
                    participant_id=participant_id,
                    price=25,
                    cancelled=False,
                )
            )
