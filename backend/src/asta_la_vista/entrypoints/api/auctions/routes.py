from flask import make_response, render_template
from flask.views import MethodView
from werkzeug.utils import secure_filename

from asta_la_vista.domain import commands
from asta_la_vista.entrypoints.flask_app import bus, uow
from asta_la_vista.exceptions import ValidationError
from asta_la_vista.views import auctions

from . import blueprint
from .schemas import (
    AuctionCreateSchema,
    AuctionDetailSchema,
    AuctionIdSchema,
    AuctionSummarySchema,
    PurchaseCreateSchema,
    PurchaseUpdateSchema,
)


@blueprint.route("/auctions")
class AuctionCollection(MethodView):
    @blueprint.response(200, AuctionSummarySchema(many=True))
    def get(self) -> list[dict]:
        return auctions.auction_list(uow())

    @blueprint.arguments(AuctionCreateSchema)
    @blueprint.response(201, AuctionIdSchema)
    def post(self, body: dict) -> dict[str, str]:
        auction_id = bus().handle(
            commands.CreateAuction(
                name=body["name"],
                initial_credits=body["initial_credits"],
                goalkeeper_slots=body["goalkeeper_slots"],
                defender_slots=body["defender_slots"],
                midfielder_slots=body["midfielder_slots"],
                forward_slots=body["forward_slots"],
                participant_names=tuple(body["participant_names"]),
                strategy_id=body.get("strategy_id"),
            )
        )
        return {"id": auction_id}


@blueprint.route("/auctions/<string:auction_id>")
class AuctionResource(MethodView):
    @blueprint.response(200, AuctionDetailSchema)
    def get(self, auction_id: str) -> dict:
        return auctions.auction_detail(uow(), auction_id)

    @blueprint.response(204)
    def delete(self, auction_id: str):
        bus().handle(commands.DeleteAuction(auction_id))


@blueprint.route("/auctions/<string:auction_id>/report")
class AuctionReport(MethodView):
    def get(self, auction_id: str):
        auction = auctions.auction_detail(uow(), auction_id)
        if auction["status"] != "completed":
            raise ValidationError("Auction must be completed before exporting a report")
        response = make_response(render_template("auction_report.html", auction=auction))
        filename = secure_filename(auction["name"]) or "auction"
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}.html"'
        response.mimetype = "text/html"
        return response


@blueprint.route("/auctions/<string:auction_id>/start")
class AuctionStart(MethodView):
    @blueprint.response(204)
    def post(self, auction_id: str):
        bus().handle(commands.StartAuction(auction_id))


@blueprint.route("/auctions/<string:auction_id>/complete")
class AuctionComplete(MethodView):
    @blueprint.response(204)
    def post(self, auction_id: str):
        bus().handle(commands.CompleteAuction(auction_id))


@blueprint.route("/auctions/<string:auction_id>/reopen")
class AuctionReopen(MethodView):
    @blueprint.response(204)
    def post(self, auction_id: str):
        bus().handle(commands.ReopenAuction(auction_id))


@blueprint.route("/auctions/<string:auction_id>/purchases")
class PurchaseCollection(MethodView):
    @blueprint.arguments(PurchaseCreateSchema)
    @blueprint.response(201, AuctionIdSchema)
    def post(self, body: dict, auction_id: str) -> dict[str, str]:
        purchase_id = bus().handle(
            commands.RecordPurchase(
                auction_id, body["player_id"], body["participant_id"], body["price"]
            )
        )
        return {"id": purchase_id}


@blueprint.route("/auctions/<string:auction_id>/purchases/<string:purchase_id>")
class PurchaseResource(MethodView):
    @blueprint.arguments(PurchaseUpdateSchema)
    @blueprint.response(204)
    def patch(self, body: dict, auction_id: str, purchase_id: str):
        bus().handle(
            commands.AmendPurchase(auction_id, purchase_id, body["participant_id"], body["price"])
        )

    @blueprint.response(204)
    def delete(self, auction_id: str, purchase_id: str):
        bus().handle(commands.CancelPurchase(auction_id, purchase_id))
