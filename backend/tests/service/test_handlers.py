import pytest

from asta_la_vista import bootstrap
from asta_la_vista.domain import commands
from asta_la_vista.domain.model import Player, Role
from asta_la_vista.exceptions import ValidationError
from asta_la_vista.service_layer.unit_of_work import SqlAlchemyUnitOfWork


def test_auction_purchase_flow_runs_through_the_message_bus(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        uow.players.add(Player("5841", "Svilar", "Roma", Role.GOALKEEPER))
        uow.commit()

    auction_id = bus.handle(
        commands.CreateAuction(
            name="Friends league",
            initial_credits=100,
            goalkeeper_slots=1,
            defender_slots=2,
            midfielder_slots=2,
            forward_slots=1,
            participant_names=("Alice", "Bob"),
        )
    )
    with uow:
        participant_id = uow.auctions.get(auction_id).participants[0].uuid
    bus.handle(commands.StartAuction(auction_id))
    purchase_id = bus.handle(commands.RecordPurchase(auction_id, "5841", participant_id, 20))

    with uow:
        auction = uow.auctions.get(auction_id)
        assert purchase_id == auction.purchases[0].uuid
        assert auction.purchases[0].player_name == "Svilar"
        assert auction.purchases[0].role == Role.GOALKEEPER
        assert auction.remaining_credits(participant_id) == 80


def test_inactive_player_cannot_be_purchased(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        player = Player("5841", "Svilar", "Roma", Role.GOALKEEPER)
        player.deactivate()
        uow.players.add(player)
        uow.commit()
    auction_id = bus.handle(commands.CreateAuction("League", 10, 1, 0, 0, 0, ("Alice",)))
    with uow:
        participant_id = uow.auctions.get(auction_id).participants[0].uuid
    bus.handle(commands.StartAuction(auction_id))

    with pytest.raises(ValidationError):
        bus.handle(commands.RecordPurchase(auction_id, "5841", participant_id, 1))


def test_strategy_flow_uses_the_player_current_role(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        uow.players.add(Player("2764", "Martinez L.", "Inter", Role.FORWARD))
        uow.commit()

    strategy_id = bus.handle(commands.CreateStrategy("Main strategy"))
    tier_id = bus.handle(commands.AddTier(strategy_id, "Top", "#ef4444"))
    bus.handle(commands.UpdateStrategyPlayer(strategy_id, "2764", tier_id, "Primary target", 15.5))

    with uow:
        strategy = uow.strategies.get(strategy_id)
        assert strategy.entries[0].role == Role.FORWARD
        assert strategy.entries[0].tier_id == tier_id
        assert strategy.entries[0].note == "Primary target"
        assert strategy.entries[0].maximum_price_percentage == 15.5


def test_strategy_can_be_deleted(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)

    strategy_id = bus.handle(commands.CreateStrategy("Main strategy"))
    bus.handle(commands.DeleteStrategy(strategy_id))

    with uow:
        assert uow.strategies.get(strategy_id) is None
