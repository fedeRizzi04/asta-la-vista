import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url


def load_settings() -> dict[str, object]:
    load_dotenv()
    return {
        "DATABASE_URI": _required("DATABASE_URI"),
        "APP_HOST": _required("APP_HOST"),
        "APP_PORT": int(_required("APP_PORT")),
        "API_TITLE": _required("API_TITLE"),
        "API_VERSION": _required("API_VERSION"),
        "OPENAPI_VERSION": _required("OPENAPI_VERSION"),
        "OPENAPI_URL_PREFIX": "/api/docs",
        "OPENAPI_SWAGGER_UI_PATH": "/swagger",
        "OPENAPI_SWAGGER_UI_URL": "https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    }


def ensure_instance_directory(app_instance_path: str):
    Path(app_instance_path).mkdir(parents=True, exist_ok=True)


def database_uri() -> str:
    load_dotenv()
    uri = _required("DATABASE_URI")
    _ensure_database_directory(uri)
    return uri


def _ensure_database_directory(uri: str) -> None:
    url = make_url(uri)
    if url.get_backend_name() != "sqlite" or url.database in {None, "", ":memory:"}:
        return
    Path(url.database).expanduser().parent.mkdir(parents=True, exist_ok=True)


def _required(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
