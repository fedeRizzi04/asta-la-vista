from flask_smorest import Blueprint

blueprint = Blueprint("auctions", __name__, url_prefix="/api", description="Auctions")

from . import routes  # noqa: E402,F401
