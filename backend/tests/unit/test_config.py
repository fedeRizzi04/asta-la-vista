import stat

import pytest
from sqlalchemy.engine import make_url

from asta_la_vista import config


def test_relative_sqlite_database_is_resolved_from_backend_root(tmp_path, monkeypatch):
    backend_root = tmp_path / "backend"
    working_directory = tmp_path / "elsewhere"
    backend_root.mkdir()
    working_directory.mkdir()
    monkeypatch.setattr(config, "BACKEND_ROOT", backend_root)
    monkeypatch.setenv("DATABASE_URI", "sqlite:///instance/database.sqlite3")
    monkeypatch.chdir(working_directory)

    uri = config.database_uri()
    database_path = backend_root / "instance" / "database.sqlite3"

    assert make_url(uri).database == str(database_path)
    assert database_path.parent.is_dir()
    assert stat.S_IMODE(database_path.parent.stat().st_mode) == 0o700


def test_non_sqlite_database_uri_is_unchanged(monkeypatch):
    uri = "postgresql://user:password@database.example/app"
    monkeypatch.setenv("DATABASE_URI", uri)

    assert config.database_uri() == uri


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, False),
        ("", False),
        ("false", False),
        ("0", False),
        ("true", True),
        (" TRUE ", True),
        ("1", True),
        ("yes", True),
    ],
)
def test_update_check_is_off_unless_enabled(monkeypatch, value, expected):
    monkeypatch.setattr(config, "load_dotenv", lambda _path: None)
    for name, default in {
        "DATABASE_URI": "sqlite://",
        "APP_HOST": "127.0.0.1",
        "APP_PORT": "5000",
        "API_TITLE": "T",
        "API_VERSION": "v1",
        "OPENAPI_VERSION": "3.1.0",
    }.items():
        monkeypatch.setenv(name, default)
    if value is None:
        monkeypatch.delenv("UPDATE_CHECK", raising=False)
    else:
        monkeypatch.setenv("UPDATE_CHECK", value)

    assert config.load_settings()["UPDATE_CHECK"] is expected
