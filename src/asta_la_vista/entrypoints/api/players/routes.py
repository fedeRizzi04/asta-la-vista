from flask import request
from flask.views import MethodView

from asta_la_vista.adapters.player_file import parse_player_file
from asta_la_vista.domain import commands
from asta_la_vista.domain.model import Role
from asta_la_vista.entrypoints.flask_app import bus, uow
from asta_la_vista.exceptions import ValidationError
from asta_la_vista.views import players

from . import blueprint
from .schemas import (
    ImportQuerySchema,
    ImportSummarySchema,
    PlayerCountsSchema,
    PlayerQuerySchema,
    PlayerSchema,
)


@blueprint.route("/players")
class PlayerCollection(MethodView):
    @blueprint.arguments(PlayerQuerySchema, location="query")
    @blueprint.response(200, PlayerSchema(many=True))
    def get(self, query: dict) -> list[dict]:
        role = Role(query["role"]) if query.get("role") else None
        active = None if query["include_inactive"] else True
        return players.player_list(uow(), role=role, search=query.get("search"), active=active)


@blueprint.route("/players/counts")
class PlayerCounts(MethodView):
    @blueprint.response(200, PlayerCountsSchema)
    def get(self) -> dict[str, int]:
        return players.player_counts(uow())


@blueprint.route("/players/import")
class PlayerImport(MethodView):
    @blueprint.arguments(ImportQuerySchema, location="query")
    @blueprint.response(200, ImportSummarySchema)
    def post(self, query: dict) -> dict[str, int]:
        uploaded_file = request.files.get("file")
        if uploaded_file is None or not uploaded_file.filename:
            raise ValidationError("A .xlsx or .csv player list is required")
        rows = parse_player_file(uploaded_file.read(), uploaded_file.filename)
        return bus().handle(commands.ImportPlayers(rows, query["confirm_live"]))
