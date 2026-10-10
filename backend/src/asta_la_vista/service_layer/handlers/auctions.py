from asta_la_vista.domain import commands, model
from asta_la_vista.exceptions import NotFoundError, ValidationError
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork


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


def delete_auction(cmd: commands.DeleteAuction, uow: AbstractUnitOfWork):
    with uow:
        auction = _auction(uow, cmd.auction_id)
        uow.auctions.remove(auction)
        uow.commit()


def set_auction_strategy(cmd: commands.SetAuctionStrategy, uow: AbstractUnitOfWork):
    with uow:
        auction = _auction(uow, cmd.auction_id)
        if cmd.strategy_id is not None and uow.strategies.get(cmd.strategy_id) is None:
            raise NotFoundError("Strategy not found")
        auction.set_strategy(cmd.strategy_id)
        uow.commit()


def _auction(uow: AbstractUnitOfWork, auction_id: str) -> model.Auction:
    auction = uow.auctions.get(auction_id)
    if auction is None:
        raise NotFoundError("Auction not found")
    return auction
