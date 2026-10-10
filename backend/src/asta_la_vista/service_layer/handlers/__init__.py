from asta_la_vista.domain import commands, events
from asta_la_vista.service_layer.handlers import auctions, players, strategies

COMMAND_HANDLERS = {
    commands.ImportPlayers: players.import_players,
    commands.CreateAuction: auctions.create_auction,
    commands.StartAuction: auctions.start_auction,
    commands.RecordPurchase: auctions.record_purchase,
    commands.AmendPurchase: auctions.amend_purchase,
    commands.CancelPurchase: auctions.cancel_purchase,
    commands.CompleteAuction: auctions.complete_auction,
    commands.ReopenAuction: auctions.reopen_auction,
    commands.DeleteAuction: auctions.delete_auction,
    commands.SetAuctionStrategy: auctions.set_auction_strategy,
    commands.CreateStrategy: strategies.create_strategy,
    commands.RenameStrategy: strategies.rename_strategy,
    commands.DeleteStrategy: strategies.delete_strategy,
    commands.AddTier: strategies.add_tier,
    commands.UpdateTier: strategies.update_tier,
    commands.RemoveTier: strategies.remove_tier,
    commands.ReorderTiers: strategies.reorder_tiers,
    commands.UpdateStrategyPlayer: strategies.update_strategy_player,
    commands.DuplicateStrategy: strategies.duplicate_strategy,
    commands.ImportStrategy: strategies.import_strategy,
}
EVENT_HANDLERS: dict[type[events.Event], list] = {}
