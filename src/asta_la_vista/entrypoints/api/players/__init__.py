from flask_smorest import Blueprint

blueprint = Blueprint("players", __name__, url_prefix="/api", description="Player catalog")

from . import routes  # noqa: E402,F401
