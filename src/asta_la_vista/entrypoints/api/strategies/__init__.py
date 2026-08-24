from flask_smorest import Blueprint

blueprint = Blueprint("strategies", __name__, url_prefix="/api", description="Strategies")

from . import routes  # noqa: E402,F401
