"""Asta la Vista backend."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("asta-la-vista")
except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled checkout
    __version__ = "0.0.0+unknown"
