from asta_la_vista.adapters.strategy_file import StrategyExport, StrategyExportRow
from asta_la_vista.domain.model import Auction, Player, Role, RosterSlots, Strategy
from asta_la_vista.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from asta_la_vista.views import auctions, players, strategies


def test_player_views_filter_by_role_search_and_activity(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    with uow:
        uow.players.add(
            Player("1", "Svilar", "Roma", Role.GOALKEEPER, quotation=18, mantra_roles=("Por",))
        )
        uow.players.add(Player("2", "Sommer", "Inter", Role.GOALKEEPER, active=False))
        uow.players.add(Player("3", "Martinez", "Inter", Role.FORWARD))
        uow.commit()

    assert players.player_list(uow, role=Role.GOALKEEPER) == [
        {
            "id": "1",
            "name": "Svilar",
            "team": "Roma",
            "role": "P",
            "quotation": 18,
            "mantra_roles": ["Por"],
            "active": True,
        }
    ]
    assert [player["id"] for player in players.player_list(uow, search="inter", active=None)] == [
        "2",
        "3",
    ]
    assert players.player_counts(uow) == {"P": 1, "D": 0, "C": 0, "A": 1}


def test_strategy_detail_contains_player_team_status_tiers_and_notes(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    with uow:
        player = Player("1", "Martinez", "Inter", Role.FORWARD, mantra_roles=("Pc", "A"))
        strategy = Strategy("Main", uuid="strategy-1")
        tier_id = strategy.add_tier("Top", "#ef4444", uuid="tier-1")
        strategy.assign_player(player.external_id, player.role, tier_id)
        strategy.set_player_note(player.external_id, player.role, "Primary target")
        uow.players.add(player)
        uow.strategies.add(strategy)
        uow.commit()

    detail = strategies.strategy_detail(uow, "strategy-1")

    assert detail["tiers"] == [{"id": "tier-1", "name": "Top", "position": 0, "color": "#ef4444"}]
    assert detail["entries"] == [
        {
            "player_id": "1",
            "name": "Martinez",
            "team": "Inter",
            "role": "A",
            "active": True,
            "mantra_roles": ["Pc", "A"],
            "tier_id": "tier-1",
            "note": "Primary target",
            "maximum_price_percentage": None,
        }
    ]


def test_strategy_export_orders_tiers_and_keeps_note_only_entries(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    with uow:
        first_player = Player("1", "Zaccagni", "Lazio", Role.MIDFIELDER)
        second_player = Player("2", "Martinez", "Inter", Role.FORWARD)
        note_only_player = Player("3", "Svilar", "Roma", Role.GOALKEEPER)
        strategy = Strategy("Main", uuid="strategy-1")
        second_tier_id = strategy.add_tier("Seconda", "#123456", uuid="tier-2")
        first_tier_id = strategy.add_tier("Prima", uuid="tier-1")
        strategy.reorder_tiers([first_tier_id, second_tier_id])
        strategy.update_player(first_player.external_id, first_player.role, second_tier_id, "", 4.0)
        strategy.update_player(
            second_player.external_id, second_player.role, first_tier_id, "Rigorista", 8.5
        )
        strategy.update_player(
            note_only_player.external_id, note_only_player.role, None, "Da monitorare", None
        )
        for player in (first_player, second_player, note_only_player):
            uow.players.add(player)
        uow.strategies.add(strategy)
        uow.commit()

    exported = strategies.strategy_export(uow, "strategy-1")

    assert exported == StrategyExport(
        "Main",
        (
            StrategyExportRow("Martinez", "Prima", None, 8.5, "Rigorista"),
            StrategyExportRow("Zaccagni", "Seconda", "#123456", 4.0, ""),
            StrategyExportRow("Svilar", "", None, None, "Da monitorare"),
        ),
    )


def test_auction_detail_calculates_rosters_credits_slots_and_maximum_bid(session_factory):
    uow = SqlAlchemyUnitOfWork(session_factory)
    with uow:
        player = Player("1", "Svilar", "Roma", Role.GOALKEEPER, mantra_roles=("Por",))
        auction = Auction("League", 100, RosterSlots(1, 2, 2, 1), uuid="auction-1")
        alice_id = auction.add_participant("Alice", uuid="alice")
        auction.add_participant("Bob", uuid="bob")
        auction.start()
        auction.record_purchase(
            player.external_id,
            player.name,
            player.role,
            alice_id,
            20,
            uuid="purchase-1",
        )
        uow.players.add(player)
        uow.auctions.add(auction)
        uow.commit()

    detail = auctions.auction_detail(uow, "auction-1")

    alice, bob = detail["participants"]
    assert (alice["name"], alice["credits_remaining"], alice["maximum_bid"]) == (
        "Alice",
        80,
        76,
    )
    assert alice["slots"]["P"] == {"filled": 1, "total": 1}
    purchase = alice["purchases"][0]
    assert purchase.pop("created_at")
    assert purchase == {
        "id": "purchase-1",
        "player_id": "1",
        "player_name": "Svilar",
        "team": "Roma",
        "role": "P",
        "price": 20,
        "player_active": True,
        "mantra_roles": ["Por"],
    }
    assert (bob["name"], bob["credits_remaining"], bob["maximum_bid"]) == ("Bob", 100, 95)
    assert detail["purchased_player_ids"] == ["1"]
