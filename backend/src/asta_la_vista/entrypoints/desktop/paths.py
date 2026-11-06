"""Where the desktop app reads its bundled resources and writes the user's data."""

import os
import sys
from pathlib import Path

APP_NAME = "Asta la Vista"
DATA_DIR_ENV = "ASTA_LA_VISTA_DATA_DIR"

_REPOSITORY_ROOT = Path(__file__).resolve().parents[5]


def is_frozen() -> bool:
    """True when running inside an executable built by PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    """Folder holding ``frontend/`` and ``migrations/``.

    PyInstaller unpacks bundled files into ``sys._MEIPASS``; from a checkout they live in the
    repository (the frontend only after ``npm run build``).
    """
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return _REPOSITORY_ROOT


def frontend_dist() -> Path:
    root = resource_root()
    return root / "frontend" if is_frozen() else root / "frontend" / "build"


def migrations_dir() -> Path:
    root = resource_root()
    return root / "migrations" if is_frozen() else root / "backend" / "migrations"


def data_dir() -> Path:
    """Per-user folder for the database, the log and the running-instance file.

    - macOS: ``~/Library/Application Support/Asta la Vista``
    - Windows: ``%APPDATA%\\Asta la Vista``
    - elsewhere: ``$XDG_DATA_HOME/asta-la-vista`` (or ``~/.local/share/asta-la-vista``)
    """
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        return (Path(appdata) if appdata else Path.home() / "AppData" / "Roaming") / APP_NAME
    xdg = os.environ.get("XDG_DATA_HOME")
    return (Path(xdg) if xdg else Path.home() / ".local" / "share") / "asta-la-vista"
