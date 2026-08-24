from asta_la_vista.domain import commands, events, model
from asta_la_vista.exceptions import NotFoundError, ValidationError
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork


def import_players(cmd: commands.ImportPlayers, uow: AbstractUnitOfWork) -> dict[str, int]:
    if not cmd.players:
        raise ValidationError("The player list is empty")
    incoming_ids = [row.external_id for row in cmd.players]
    if len(incoming_ids) != len(set(incoming_ids)):
        raise ValidationError("The player list contains duplicate ids")
    with uow:
        if uow.auctions.has_live() and not cmd.allow_live_auction:
            raise ValidationError("A live auction requires explicit import confirmation")
        existing = {player.external_id: player for player in uow.players.list_all()}
        added = updated = deactivated = role_changes = 0
        for row in cmd.players:
            try:
                role = model.Role(row.role)
            except ValueError as exc:
                raise ValidationError(f"Unsupported Classic role: {row.role}") from exc
            player = existing.get(row.external_id)
            if player is None:
                uow.players.add(model.Player(row.external_id, row.name, row.team, role))
                added += 1
                continue
            changed = (player.name, player.team, player.role, player.active) != (
                row.name.strip(),
                row.team.strip(),
                role,
                True,
            )
            previous_role = player.role
            player.update(row.name, row.team, role)
            updated += changed
            if previous_role != role:
                role_changes += 1
                for strategy in uow.strategies.list_containing_player(player.external_id):
                    strategy.change_player_role(player.external_id, role)
        incoming = set(incoming_ids)
        for player_id, player in existing.items():
            if player_id not in incoming and player.active:
                player.deactivate()
                deactivated += 1
        uow.commit()
    return {
        "added": added,
        "updated": updated,
        "deactivated": deactivated,
        "role_changes": role_changes,
    }


def create_auction(cmd: commands.CreateAuction, uow: AbstractUnitOfWork) -> str:
    slots = model.RosterSlots(
        cmd.goalkeeper_slots, cmd.defender_slots, cmd.midfielder_slots, cmd.forward_slots
    )
    with uow:
        if cmd.strategy_id is not None and uow.strategies.get(cmd.strategy_id) is None:
            raise NotFoundError("Strategy not found")
        auction = model.Auction(cmd.name, cmd.initial_credits, slots, strategy_id=cmd.strategy_id)
        for participant_name in cmd.participant_names:
            auction.add_participant(participant_name)
        uow.auctions.add(auction)
        auction_id = auction.uuid
        uow.commit()
    return auction_id


def start_auction(cmd: commands.StartAuction, uow: AbstractUnitOfWork):
    with uow:
        auction = _auction(uow, cmd.auction_id)
        auction.start()
        uow.commit()


def record_purchase(cmd: commands.RecordPurchase, uow: AbstractUnitOfWork) -> str:
    with uow:
        auction = _auction(uow, cmd.auction_id)
        player = uow.players.get(cmd.player_id)
        if player is None:
            raise NotFoundError("Player not found")
        if not player.active:
            raise ValidationError("Inactive players cannot be purchased")
        purchase_id = auction.record_purchase(
            player.external_id,
            player.name,
            player.role,
            cmd.participant_id,
            cmd.price,
        )
        uow.commit()
    return purchase_id


def amend_purchase(cmd: commands.AmendPurchase, uow: AbstractUnitOfWork):
    with uow:
        auction = _auction(uow, cmd.auction_id)
        auction.amend_purchase(cmd.purchase_id, cmd.participant_id, cmd.price)
        uow.commit()


def cancel_purchase(cmd: commands.CancelPurchase, uow: AbstractUnitOfWork):
    with uow:
        auction = _auction(uow, cmd.auction_id)
        auction.cancel_purchase(cmd.purchase_id)
        uow.commit()


def complete_auction(cmd: commands.CompleteAuction, uow: AbstractUnitOfWork):
    with uow:
        auction = _auction(uow, cmd.auction_id)
        auction.complete()
        uow.commit()


def reopen_auction(cmd: commands.ReopenAuction, uow: AbstractUnitOfWork):
    with uow:
        auction = _auction(uow, cmd.auction_id)
        auction.reopen()
        uow.commit()


def create_strategy(cmd: commands.CreateStrategy, uow: AbstractUnitOfWork) -> str:
    with uow:
        strategy = model.Strategy(cmd.name)
        uow.strategies.add(strategy)
        strategy_id = strategy.uuid
        uow.commit()
    return strategy_id


def add_tier(cmd: commands.AddTier, uow: AbstractUnitOfWork) -> str:
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        tier_id = strategy.add_tier(model.Role(cmd.role), cmd.name, cmd.color)
        uow.commit()
    return tier_id


def assign_player_to_tier(cmd: commands.AssignPlayerToTier, uow: AbstractUnitOfWork):
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        player = uow.players.get(cmd.player_id)
        if player is None:
            raise NotFoundError("Player not found")
        strategy.assign_player(player.external_id, player.role, cmd.tier_id)
        uow.commit()


def set_strategy_player_note(cmd: commands.SetStrategyPlayerNote, uow: AbstractUnitOfWork):
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        player = uow.players.get(cmd.player_id)
        if player is None:
            raise NotFoundError("Player not found")
        strategy.set_player_note(player.external_id, player.role, cmd.note)
        uow.commit()


def duplicate_strategy(cmd: commands.DuplicateStrategy, uow: AbstractUnitOfWork) -> str:
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        duplicate = strategy.duplicate(cmd.name)
        uow.strategies.add(duplicate)
        duplicate_id = duplicate.uuid
        uow.commit()
    return duplicate_id


def _auction(uow: AbstractUnitOfWork, auction_id: str) -> model.Auction:
    auction = uow.auctions.get(auction_id)
    if auction is None:
        raise NotFoundError("Auction not found")
    return auction


def _strategy(uow: AbstractUnitOfWork, strategy_id: str) -> model.Strategy:
    strategy = uow.strategies.get(strategy_id)
    if strategy is None:
        raise NotFoundError("Strategy not found")
    return strategy


COMMAND_HANDLERS = {
    commands.ImportPlayers: import_players,
    commands.CreateAuction: create_auction,
    commands.StartAuction: start_auction,
    commands.RecordPurchase: record_purchase,
    commands.AmendPurchase: amend_purchase,
    commands.CancelPurchase: cancel_purchase,
    commands.CompleteAuction: complete_auction,
    commands.ReopenAuction: reopen_auction,
    commands.CreateStrategy: create_strategy,
    commands.AddTier: add_tier,
    commands.AssignPlayerToTier: assign_player_to_tier,
    commands.SetStrategyPlayerNote: set_strategy_player_note,
    commands.DuplicateStrategy: duplicate_strategy,
}
EVENT_HANDLERS: dict[type[events.Event], list] = {}
