from flask.views import MethodView

from . import blueprint
from .schemas import HealthSchema


@blueprint.route("/health")
class HealthResource(MethodView):
    @blueprint.response(200, HealthSchema)
    def get(self) -> dict[str, str]:
        return {"status": "ok"}
