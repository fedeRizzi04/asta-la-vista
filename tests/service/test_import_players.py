import pytest

from asta_la_vista import bootstrap
from asta_la_vista.domain import commands
from asta_la_vista.domain.model import Player, Role, Strategy
from asta_la_vista.exceptions import ValidationError
from asta_la_vista.service_layer.unit_of_work import SqlAlchemyUnitOfWork


def test_import_adds_updates_and_deactivates_players(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        uow.players.add(Player("1", "Old name", "Old team", Role.DEFENDER))
        uow.players.add(Player("2", "Leaving", "Team", Role.FORWARD))
        strategy = Strategy("Main")
        tier_id = strategy.add_tier(Role.DEFENDER, "Top")
        strategy.assign_player("1", Role.DEFENDER, tier_id)
        strategy.set_player_note("1", Role.DEFENDER, "Keep this note")
        uow.strategies.add(strategy)
        strategy_id = strategy.uuid
        uow.commit()

    summary = bus.handle(
        commands.ImportPlayers(
            (
                commands.PlayerRow("1", "New name", "New team", "C"),
                commands.PlayerRow("3", "New player", "Team", "A"),
            )
        )
    )

    assert summary == {"added": 1, "updated": 1, "deactivated": 1, "role_changes": 1}
    with uow:
        assert uow.players.get("1").role == Role.MIDFIELDER
        assert uow.players.get("2").active is False
        assert uow.players.get("3").team == "Team"
        entry = uow.strategies.get(strategy_id).entries[0]
        assert (entry.role, entry.tier_id, entry.note) == (
            Role.MIDFIELDER,
            None,
            "Keep this note",
        )


def test_import_during_live_auction_requires_explicit_confirmation(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    auction_id = bus.handle(commands.CreateAuction("League", 10, 1, 0, 0, 0, ("Alice",)))
    bus.handle(commands.StartAuction(auction_id))
    import_command = commands.ImportPlayers((commands.PlayerRow("1", "Player", "Team", "P"),))

    with pytest.raises(ValidationError):
        bus.handle(import_command)

    summary = bus.handle(commands.ImportPlayers(import_command.players, allow_live_auction=True))
    assert summary["added"] == 1
