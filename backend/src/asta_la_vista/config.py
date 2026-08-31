import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_ROOT / ".env"


def load_settings() -> dict[str, object]:
    load_dotenv(ENV_FILE)
    return {
        "DATABASE_URI": _prepare_database_uri(_required("DATABASE_URI")),
        "APP_HOST": _required("APP_HOST"),
        "APP_PORT": int(_required("APP_PORT")),
        "FRONTEND_DIST": os.getenv("FRONTEND_DIST"),
        "API_TITLE": _required("API_TITLE"),
        "API_VERSION": _required("API_VERSION"),
        "OPENAPI_VERSION": _required("OPENAPI_VERSION"),
        "OPENAPI_URL_PREFIX": "/api/docs",
        "OPENAPI_SWAGGER_UI_PATH": "/swagger",
        "OPENAPI_SWAGGER_UI_URL": "https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    }


def database_uri() -> str:
    load_dotenv(ENV_FILE)
    return _prepare_database_uri(_required("DATABASE_URI"))


def _prepare_database_uri(uri: str) -> str:
    url = make_url(uri)
    if url.get_backend_name() != "sqlite" or url.database in {None, "", ":memory:"}:
        return uri

    database_path = Path(url.database).expanduser()
    if not database_path.is_absolute():
        database_path = BACKEND_ROOT / database_path
    database_path = database_path.resolve()
    database_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    return url.set(database=str(database_path)).render_as_string(hide_password=False)


def _required(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
