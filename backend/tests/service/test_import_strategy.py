import pytest
import sqlalchemy as sa

from asta_la_vista import bootstrap
from asta_la_vista.domain import commands
from asta_la_vista.domain.model import Player, Role
from asta_la_vista.exceptions import ConfirmationRequiredError, ValidationError
from asta_la_vista.service_layer.unit_of_work import SqlAlchemyUnitOfWork


def test_import_creates_tiers_in_order_and_assigns_players(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        uow.players.add(Player("1", "Lautaro", "Inter", Role.FORWARD))
        uow.players.add(Player("2", "Some Backup", "Roma", Role.MIDFIELDER))
        uow.commit()

    summary = bus.handle(
        commands.ImportStrategy(
            "Fasce importate",
            (
                commands.TierImportRow("Lautaro", "Top", "Rigorista", 5.8),
                commands.TierImportRow("Some Backup", "", "Da monitorare a fine mercato", 3.2),
            ),
        )
    )

    assert summary["tiers_created"] == 1
    assert summary["players_assigned"] == 2
    assert summary["unmatched"] == []
    with uow:
        strategy = uow.strategies.get(summary["strategy_id"])
        assert strategy.name == "Fasce importate"
        [tier] = strategy.tiers
        assert tier.name == "Top"
        lautaro = next(entry for entry in strategy.entries if entry.player_id == "1")
        assert (lautaro.tier_id, lautaro.note, float(lautaro.maximum_price_percentage)) == (
            tier.uuid,
            "Rigorista",
            5.8,
        )
        backup = next(entry for entry in strategy.entries if entry.player_id == "2")
        assert (backup.tier_id, backup.note, float(backup.maximum_price_percentage)) == (
            None,
            "Da monitorare a fine mercato",
            3.2,
        )


def test_repeated_fascia_reuses_the_same_tier(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        uow.players.add(Player("1", "Lautaro", "Inter", Role.FORWARD))
        uow.players.add(Player("2", "Thuram", "Inter", Role.FORWARD))
        uow.commit()

    summary = bus.handle(
        commands.ImportStrategy(
            "Fasce importate",
            (
                commands.TierImportRow("Lautaro", "Top"),
                commands.TierImportRow("Thuram", "Top"),
            ),
        )
    )

    assert summary["tiers_created"] == 1
    assert summary["players_assigned"] == 2


def test_import_requires_confirmation_without_creating_anything_when_a_player_is_not_found(
    session_factory,
):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        uow.players.add(Player("1", "Lautaro", "Inter", Role.FORWARD))
        uow.commit()
    import_command = commands.ImportStrategy(
        "Fasce importate",
        (
            commands.TierImportRow("Lautaro", "Top"),
            commands.TierImportRow("Ignoto", "Top"),
        ),
    )

    with pytest.raises(ConfirmationRequiredError, match="Ignoto"):
        bus.handle(import_command)

    with uow:
        assert uow.session.execute(sa.text("SELECT COUNT(*) FROM strategy")).scalar() == 0


def test_import_skips_unmatched_players_once_confirmed(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        uow.players.add(Player("1", "Lautaro", "Inter", Role.FORWARD))
        uow.commit()
    import_command = commands.ImportStrategy(
        "Fasce importate",
        (
            commands.TierImportRow("Lautaro", "Top"),
            commands.TierImportRow("Ignoto", "Top"),
        ),
    )

    summary = bus.handle(
        commands.ImportStrategy(
            import_command.name, import_command.rows, allow_unmatched_players=True
        )
    )

    assert summary["players_assigned"] == 1
    assert summary["unmatched"] == ["Ignoto"]
    with uow:
        strategy = uow.strategies.get(summary["strategy_id"])
        [entry] = strategy.entries
        assert entry.player_id == "1"


def test_row_with_neither_fascia_nor_note_is_skipped(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        uow.players.add(Player("1", "Lautaro", "Inter", Role.FORWARD))
        uow.commit()

    summary = bus.handle(
        commands.ImportStrategy("Fasce importate", (commands.TierImportRow("Lautaro"),))
    )

    assert summary["players_assigned"] == 0
    assert summary["unmatched"] == []
    with uow:
        strategy = uow.strategies.get(summary["strategy_id"])
        assert strategy.entries == []


def test_import_rejects_a_name_already_taken_by_another_strategy(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    bus = bootstrap.bootstrap(uow)
    with uow:
        uow.players.add(Player("1", "Lautaro", "Inter", Role.FORWARD))
        uow.commit()
    bus.handle(commands.CreateStrategy("Prova"))

    with pytest.raises(ValidationError, match='A strategy named "Prova" already exists'):
        bus.handle(commands.ImportStrategy("Prova", (commands.TierImportRow("Lautaro", "Top"),)))
