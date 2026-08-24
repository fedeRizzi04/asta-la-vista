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


def test_strategy_has_independent_ordered_tiers_for_each_role():
    strategy = Strategy("Main strategy")
    first = strategy.add_tier(Role.FORWARD, "Top", "#ef4444", uuid="first")
    second = strategy.add_tier(Role.FORWARD, "Good", "#f59e0b", uuid="second")
    goalkeeper = strategy.add_tier(Role.GOALKEEPER, "Reliable", uuid="goalkeeper")

    strategy.reorder_tiers(Role.FORWARD, [second, first])

    assert [(tier.uuid, tier.position) for tier in strategy.tiers if tier.role == Role.FORWARD] == [
        (first, 1),
        (second, 0),
    ]
    assert next(tier.position for tier in strategy.tiers if tier.uuid == goalkeeper) == 0


def test_player_can_only_be_assigned_to_a_tier_for_the_same_role():
    strategy = Strategy("Main strategy")
    forward_tier = strategy.add_tier(Role.FORWARD, "Top")

    with pytest.raises(ValidationError):
        strategy.assign_player("player-1", Role.MIDFIELDER, forward_tier)

    strategy.assign_player("player-1", Role.FORWARD, forward_tier)
    assert strategy.entries[0].tier_id == forward_tier


def test_role_change_moves_player_to_unassigned_and_keeps_note():
    strategy = Strategy("Main strategy")
    tier_id = strategy.add_tier(Role.DEFENDER, "Top")
    strategy.assign_player("player-1", Role.DEFENDER, tier_id)
    strategy.set_player_note("player-1", Role.DEFENDER, "Set-piece threat")

    strategy.change_player_role("player-1", Role.MIDFIELDER)

    entry = strategy.entries[0]
    assert (entry.role, entry.tier_id, entry.note) == (
        Role.MIDFIELDER,
        None,
        "Set-piece threat",
    )


def test_strategy_copy_can_be_changed_without_affecting_the_original():
    strategy = Strategy("Main strategy")
    tier_id = strategy.add_tier(Role.FORWARD, "Top", "#ef4444")
    strategy.assign_player("player-1", Role.FORWARD, tier_id)
    strategy.set_player_note("player-1", Role.FORWARD, "Primary target")

    duplicate = strategy.duplicate("Alternative strategy")
    duplicate.remove_tier(duplicate.tiers[0].uuid)
    duplicate.set_player_note("player-1", Role.FORWARD, "Only at a discount")

    assert strategy.tiers[0].name == "Top"
    assert strategy.entries[0].tier_id == tier_id
    assert strategy.entries[0].note == "Primary target"
    assert duplicate.entries[0].tier_id is None
