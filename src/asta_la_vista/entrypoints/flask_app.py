from flask import Flask
from flask_smorest import Api

from asta_la_vista import config


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(test_config if test_config is not None else config.load_settings())
    config.ensure_instance_directory(app.instance_path)
    Api(app)

    from asta_la_vista.entrypoints.api.system import blueprint as system_blueprint

    app.register_blueprint(system_blueprint)
    return app
