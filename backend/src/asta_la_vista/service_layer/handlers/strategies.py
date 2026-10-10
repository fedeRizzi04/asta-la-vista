from asta_la_vista.domain import commands, model
from asta_la_vista.exceptions import ConfirmationRequiredError, NotFoundError, ValidationError
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork


def create_strategy(cmd: commands.CreateStrategy, uow: AbstractUnitOfWork) -> str:
    with uow:
        _ensure_strategy_name_is_free(uow, cmd.name)
        strategy = model.Strategy(cmd.name)
        uow.strategies.add(strategy)
        strategy_id = strategy.uuid
        uow.commit()
    return strategy_id


def rename_strategy(cmd: commands.RenameStrategy, uow: AbstractUnitOfWork):
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        _ensure_strategy_name_is_free(uow, cmd.name, keeping=strategy.uuid)
        strategy.rename(cmd.name)
        uow.commit()


def delete_strategy(cmd: commands.DeleteStrategy, uow: AbstractUnitOfWork):
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        uow.strategies.remove(strategy)
        uow.commit()


def add_tier(cmd: commands.AddTier, uow: AbstractUnitOfWork) -> str:
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        tier_id = strategy.add_tier(cmd.name, cmd.color)
        uow.commit()
    return tier_id


def update_tier(cmd: commands.UpdateTier, uow: AbstractUnitOfWork):
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        strategy.update_tier(cmd.tier_id, cmd.name, cmd.color)
        uow.commit()


def remove_tier(cmd: commands.RemoveTier, uow: AbstractUnitOfWork):
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        strategy.remove_tier(cmd.tier_id)
        uow.commit()


def reorder_tiers(cmd: commands.ReorderTiers, uow: AbstractUnitOfWork):
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        strategy.reorder_tiers(list(cmd.tier_ids))
        uow.commit()


def update_strategy_player(cmd: commands.UpdateStrategyPlayer, uow: AbstractUnitOfWork):
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        player = uow.players.get(cmd.player_id)
        if player is None:
            raise NotFoundError("Player not found")
        strategy.update_player(
            player.external_id,
            player.role,
            cmd.tier_id,
            cmd.note,
            cmd.maximum_price_percentage,
        )
        uow.commit()


def import_strategy(
    cmd: commands.ImportStrategy, uow: AbstractUnitOfWork
) -> dict[str, str | int | list[str]]:
    if not cmd.rows:
        raise ValidationError("The tier list is empty")
    with uow:
        _ensure_strategy_name_is_free(uow, cmd.name)
        players_by_name = {player.name.casefold(): player for player in uow.players.list_all()}
        missing = sorted(
            {row.name for row in cmd.rows if row.name.casefold() not in players_by_name}
        )
        if missing and not cmd.allow_unmatched_players:
            raise ConfirmationRequiredError(f"No matching player found for: {', '.join(missing)}")

        strategy = model.Strategy(cmd.name)
        tier_ids: dict[str, str] = {}
        players_assigned = 0
        for row in cmd.rows:
            player = players_by_name.get(row.name.casefold())
            if player is None:
                continue
            if not row.fascia:
                if row.note or row.maximum_price_percentage is not None:
                    strategy.update_player(
                        player.external_id,
                        player.role,
                        None,
                        row.note,
                        row.maximum_price_percentage,
                    )
                    players_assigned += 1
                continue
            tier_id = tier_ids.get(row.fascia)
            if tier_id is None:
                # The row that first mentions a tier also decides its colour.
                tier_id = strategy.add_tier(row.fascia, row.colore or None)
                tier_ids[row.fascia] = tier_id
            strategy.update_player(
                player.external_id, player.role, tier_id, row.note, row.maximum_price_percentage
            )
            players_assigned += 1
        uow.strategies.add(strategy)
        strategy_id = strategy.uuid
        uow.commit()
    return {
        "strategy_id": strategy_id,
        "tiers_created": len(tier_ids),
        "players_assigned": players_assigned,
        "unmatched": missing,
    }


def duplicate_strategy(cmd: commands.DuplicateStrategy, uow: AbstractUnitOfWork) -> str:
    with uow:
        strategy = _strategy(uow, cmd.strategy_id)
        _ensure_strategy_name_is_free(uow, cmd.name)
        duplicate = strategy.duplicate(cmd.name)
        uow.strategies.add(duplicate)
        duplicate_id = duplicate.uuid
        uow.commit()
    return duplicate_id


def _ensure_strategy_name_is_free(uow: AbstractUnitOfWork, name: str, keeping: str | None = None):
    """Strategy names are unique, so reject a clash before the database does."""
    existing = uow.strategies.get_by_name(name)
    if existing is not None and existing.uuid != keeping:
        raise ValidationError(f'A strategy named "{existing.name}" already exists')


def _strategy(uow: AbstractUnitOfWork, strategy_id: str) -> model.Strategy:
    strategy = uow.strategies.get(strategy_id)
    if strategy is None:
        raise NotFoundError("Strategy not found")
    return strategy
