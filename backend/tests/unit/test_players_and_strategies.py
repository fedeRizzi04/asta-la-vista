import pytest

from asta_la_vista.domain import events
from asta_la_vista.domain.model import Player, Role, Strategy
from asta_la_vista.exceptions import ValidationError


def test_player_update_reactivates_and_reports_a_role_change():
    player = Player("5841", "Old name", "Old team", Role.DEFENDER, active=False)

    player.update("New name", "New team", Role.MIDFIELDER)

    assert player.active is True
    assert (player.name, player.team, player.role) == ("New name", "New team", Role.MIDFIELDER)
    assert list(player.events) == [events.PlayerRoleChanged("5841", Role.DEFENDER, Role.MIDFIELDER)]


def test_player_can_be_marked_inactive_without_being_deleted():
    player = Player("5841", "Player", "Team", Role.GOALKEEPER)

    player.deactivate()

    assert player.active is False
    assert list(player.events) == [events.PlayerDeactivated("5841")]


def test_player_has_an_optional_non_negative_quotation():
    player = Player("5841", "Player", "Team", Role.GOALKEEPER, quotation=18)

    player.update("Player", "Team", Role.GOALKEEPER, quotation=None)

    assert player.quotation is None
    with pytest.raises(ValidationError):
        player.update("Player", "Team", Role.GOALKEEPER, quotation=-1)


def test_strategy_has_global_ordered_tiers():
    strategy = Strategy("Main strategy")
    first = strategy.add_tier("Top", "#ef4444", uuid="first")
    second = strategy.add_tier("Good", "#f59e0b", uuid="second")

    strategy.reorder_tiers([second, first])

    assert [(tier.uuid, tier.position) for tier in strategy.tiers] == [(first, 1), (second, 0)]


def test_players_from_different_roles_can_share_a_tier():
    strategy = Strategy("Main strategy")
    tier_id = strategy.add_tier("Top")

    strategy.assign_player("player-1", Role.MIDFIELDER, tier_id)
    strategy.assign_player("player-2", Role.FORWARD, tier_id)

    assert [(entry.role, entry.tier_id) for entry in strategy.entries] == [
        (Role.MIDFIELDER, tier_id),
        (Role.FORWARD, tier_id),
    ]


def test_role_change_moves_player_to_unassigned_and_keeps_note():
    strategy = Strategy("Main strategy")
    tier_id = strategy.add_tier("Top")
    strategy.assign_player("player-1", Role.DEFENDER, tier_id)
    strategy.set_player_note("player-1", Role.DEFENDER, "Set-piece threat")

    strategy.change_player_role("player-1", Role.MIDFIELDER)

    entry = strategy.entries[0]
    assert (entry.role, entry.tier_id, entry.note) == (
        Role.MIDFIELDER,
        None,
        "Set-piece threat",
    )


def test_strategy_player_can_have_an_optional_maximum_price():
    strategy = Strategy("Main strategy")
    tier_id = strategy.add_tier("Top")

    strategy.update_player("player-1", Role.FORWARD, tier_id, "Primary target", 80)

    entry = strategy.entries[0]
    assert (entry.tier_id, entry.note, entry.maximum_price) == (tier_id, "Primary target", 80)


@pytest.mark.parametrize("maximum_price", [0, -1, 1.5, True])
def test_strategy_rejects_invalid_maximum_prices(maximum_price):
    strategy = Strategy("Main strategy")
    tier_id = strategy.add_tier("Top")

    with pytest.raises(ValidationError):
        strategy.update_player("player-1", Role.FORWARD, tier_id, "", maximum_price)


def test_maximum_price_requires_a_tier():
    strategy = Strategy("Main strategy")

    with pytest.raises(ValidationError):
        strategy.update_player("player-1", Role.FORWARD, None, "", 80)


def test_strategy_copy_can_be_changed_without_affecting_the_original():
    strategy = Strategy("Main strategy")
    tier_id = strategy.add_tier("Top", "#ef4444")
    strategy.assign_player("player-1", Role.FORWARD, tier_id)
    strategy.set_player_note("player-1", Role.FORWARD, "Primary target")
    strategy.update_player("player-1", Role.FORWARD, tier_id, "Primary target", 80)

    duplicate = strategy.duplicate("Alternative strategy")
    duplicate.remove_tier(duplicate.tiers[0].uuid)
    duplicate.set_player_note("player-1", Role.FORWARD, "Only at a discount")

    assert strategy.tiers[0].name == "Top"
    assert strategy.entries[0].tier_id == tier_id
    assert strategy.entries[0].note == "Primary target"
    assert strategy.entries[0].maximum_price == 80
    assert duplicate.entries[0].tier_id is None


def test_tier_can_be_updated_removed_and_leave_players_unassigned():
    strategy = Strategy("Main strategy")
    first = strategy.add_tier("Top", "#ef4444")
    second = strategy.add_tier("Good", "#f59e0b")
    strategy.assign_player("player-1", Role.FORWARD, first)

    strategy.update_tier(first, "Elite", "#dc2626")
    strategy.remove_tier(first)

    assert [(tier.uuid, tier.position) for tier in strategy.tiers] == [(second, 0)]
    assert strategy.entries[0].tier_id is None
