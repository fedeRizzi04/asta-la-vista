from flask_smorest import Blueprint

blueprint = Blueprint("system", __name__, url_prefix="/api", description="System status")

from . import routes  # noqa: E402,F401
