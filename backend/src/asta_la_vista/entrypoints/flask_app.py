from pathlib import Path

from flask import Flask, abort, current_app, g, send_from_directory
from flask_smorest import Api
from werkzeug.utils import safe_join

from asta_la_vista import bootstrap, config
from asta_la_vista.service_layer.messagebus import MessageBus
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork


def create_app(
    test_config: dict[str, object] | None = None,
    message_bus_factory: bootstrap.MessageBusFactory | None = None,
) -> Flask:
    app = Flask(__name__, instance_relative_config=True, static_folder=None)
    app.config.from_mapping(test_config if test_config is not None else config.load_settings())
    config.ensure_instance_directory(app.instance_path)
    api = Api(app)
    app.extensions["bus_factory"] = message_bus_factory or bootstrap.bootstrap_factory()

    from asta_la_vista.entrypoints.api.auctions import blueprint as auctions_blueprint
    from asta_la_vista.entrypoints.api.common import register_error_handlers
    from asta_la_vista.entrypoints.api.players import blueprint as players_blueprint
    from asta_la_vista.entrypoints.api.strategies import blueprint as strategies_blueprint
    from asta_la_vista.entrypoints.api.system import blueprint as system_blueprint

    api.register_blueprint(system_blueprint)
    api.register_blueprint(players_blueprint)
    api.register_blueprint(strategies_blueprint)
    api.register_blueprint(auctions_blueprint)
    register_error_handlers(app)
    _register_frontend(app)
    return app


def _register_frontend(app: Flask) -> None:
    frontend_dist_value = app.config.get("FRONTEND_DIST")
    if not frontend_dist_value:
        return

    frontend_dist = Path(str(frontend_dist_value)).resolve()
    if not (frontend_dist / "index.html").is_file():
        raise RuntimeError(f"Frontend build not found in: {frontend_dist}")

    @app.get("/")
    def frontend_index():
        return send_from_directory(frontend_dist, "index.html")

    @app.get("/<path:path>")
    def frontend_file_or_route(path: str):
        if path == "api" or path.startswith("api/"):
            abort(404)

        requested_file = safe_join(frontend_dist, path)
        if requested_file is not None and Path(requested_file).is_file():
            return send_from_directory(frontend_dist, path)
        return send_from_directory(frontend_dist, "index.html")


def bus() -> MessageBus:
    if "message_bus" not in g:
        g.message_bus = current_app.extensions["bus_factory"]()
    return g.message_bus


def uow() -> AbstractUnitOfWork:
    return bus().uow
