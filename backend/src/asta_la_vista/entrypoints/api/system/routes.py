from flask import current_app
from flask.views import MethodView

from asta_la_vista import __version__
from asta_la_vista.adapters.releases import ReleaseChecker, is_newer

from . import blueprint
from .schemas import HealthSchema, VersionSchema

# How long a request waits for GitHub; a slower answer is used by the next request.
UPDATE_CHECK_WAIT = 2.0


@blueprint.route("/health")
class HealthResource(MethodView):
    @blueprint.response(200, HealthSchema)
    def get(self) -> dict[str, str]:
        return {"status": "ok"}


@blueprint.route("/version")
class VersionResource(MethodView):
    @blueprint.response(200, VersionSchema)
    def get(self) -> dict[str, object]:
        checker: ReleaseChecker | None = current_app.extensions.get("release_checker")
        latest = checker.latest(wait=UPDATE_CHECK_WAIT) if checker is not None else None
        return {
            "version": __version__,
            "latest_version": latest.version if latest else None,
            "release_url": latest.url if latest else None,
            "update_available": latest is not None and is_newer(latest.version, __version__),
        }
