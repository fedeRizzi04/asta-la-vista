from flask import Flask
from flask_smorest import Api

from asta_la_vista import bootstrap, config
from asta_la_vista.service_layer.messagebus import MessageBus
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork


def create_app(
    test_config: dict[str, object] | None = None, message_bus: MessageBus | None = None
) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(test_config if test_config is not None else config.load_settings())
    config.ensure_instance_directory(app.instance_path)
    Api(app)
    app.extensions["bus"] = message_bus or bootstrap.bootstrap()

    from asta_la_vista.entrypoints.api.system import blueprint as system_blueprint

    app.register_blueprint(system_blueprint)
    return app


def bus() -> MessageBus:
    from flask import current_app

    return current_app.extensions["bus"]


def uow() -> AbstractUnitOfWork:
    return bus().uow
