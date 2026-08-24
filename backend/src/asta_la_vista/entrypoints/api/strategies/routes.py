from flask.views import MethodView

from asta_la_vista.domain import commands
from asta_la_vista.entrypoints.flask_app import bus, uow
from asta_la_vista.views import strategies

from . import blueprint
from .schemas import (
    StrategyCreateSchema,
    StrategyDetailSchema,
    StrategyEntryUpdateSchema,
    StrategyIdSchema,
    StrategySummarySchema,
    StrategyUpdateSchema,
    TierCreateSchema,
    TierOrderSchema,
    TierUpdateSchema,
)


@blueprint.route("/strategies")
class StrategyCollection(MethodView):
    @blueprint.response(200, StrategySummarySchema(many=True))
    def get(self) -> list[dict]:
        return strategies.strategy_list(uow())

    @blueprint.arguments(StrategyCreateSchema)
    @blueprint.response(201, StrategyIdSchema)
    def post(self, body: dict) -> dict[str, str]:
        return {"id": bus().handle(commands.CreateStrategy(body["name"]))}


@blueprint.route("/strategies/<string:strategy_id>")
class StrategyResource(MethodView):
    @blueprint.response(200, StrategyDetailSchema)
    def get(self, strategy_id: str) -> dict:
        return strategies.strategy_detail(uow(), strategy_id)

    @blueprint.arguments(StrategyUpdateSchema)
    @blueprint.response(204)
    def patch(self, body: dict, strategy_id: str):
        bus().handle(commands.RenameStrategy(strategy_id, body["name"]))


@blueprint.route("/strategies/<string:strategy_id>/duplicate")
class StrategyDuplicateResource(MethodView):
    @blueprint.arguments(StrategyCreateSchema)
    @blueprint.response(201, StrategyIdSchema)
    def post(self, body: dict, strategy_id: str) -> dict[str, str]:
        return {"id": bus().handle(commands.DuplicateStrategy(strategy_id, body["name"]))}


@blueprint.route("/strategies/<string:strategy_id>/tiers")
class TierCollection(MethodView):
    @blueprint.arguments(TierCreateSchema)
    @blueprint.response(201, StrategyIdSchema)
    def post(self, body: dict, strategy_id: str) -> dict[str, str]:
        tier_id = bus().handle(
            commands.AddTier(strategy_id, body["role"], body["name"], body.get("color"))
        )
        return {"id": tier_id}


@blueprint.route("/strategies/<string:strategy_id>/tiers/order")
class TierOrder(MethodView):
    @blueprint.arguments(TierOrderSchema)
    @blueprint.response(204)
    def put(self, body: dict, strategy_id: str):
        bus().handle(commands.ReorderTiers(strategy_id, body["role"], tuple(body["tier_ids"])))


@blueprint.route("/strategies/<string:strategy_id>/tiers/<string:tier_id>")
class TierResource(MethodView):
    @blueprint.arguments(TierUpdateSchema)
    @blueprint.response(204)
    def patch(self, body: dict, strategy_id: str, tier_id: str):
        bus().handle(commands.UpdateTier(strategy_id, tier_id, body["name"], body.get("color")))

    @blueprint.response(204)
    def delete(self, strategy_id: str, tier_id: str):
        bus().handle(commands.RemoveTier(strategy_id, tier_id))


@blueprint.route("/strategies/<string:strategy_id>/players/<string:player_id>")
class StrategyPlayerResource(MethodView):
    @blueprint.arguments(StrategyEntryUpdateSchema)
    @blueprint.response(204)
    def put(self, body: dict, strategy_id: str, player_id: str):
        if "tier_id" in body:
            command = (
                commands.AssignPlayerToTier(strategy_id, player_id, body["tier_id"])
                if body["tier_id"] is not None
                else commands.UnassignPlayerFromTier(strategy_id, player_id)
            )
            bus().handle(command)
        if body.get("note") is not None:
            bus().handle(commands.SetStrategyPlayerNote(strategy_id, player_id, body["note"]))
