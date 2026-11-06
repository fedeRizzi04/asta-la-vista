from flask.views import MethodView

from asta_la_vista import __version__

from . import blueprint
from .schemas import HealthSchema, VersionSchema


@blueprint.route("/health")
class HealthResource(MethodView):
    @blueprint.response(200, HealthSchema)
    def get(self) -> dict[str, str]:
        return {"status": "ok"}


@blueprint.route("/version")
class VersionResource(MethodView):
    @blueprint.response(200, VersionSchema)
    def get(self) -> dict[str, str]:
        return {"version": __version__}
