"""Keeps a single copy of the app running.

The running app writes its port to ``instance.json`` in the data folder. A second launch reads it,
checks that the server really answers there, and if so just opens the browser on it.
"""

import json
import urllib.request
from pathlib import Path

INSTANCE_FILE = "instance.json"


def write(data_dir: Path, port: int) -> None:
    (data_dir / INSTANCE_FILE).write_text(json.dumps({"port": port}), encoding="utf-8")


def clear(data_dir: Path) -> None:
    (data_dir / INSTANCE_FILE).unlink(missing_ok=True)


def running_url(data_dir: Path) -> str | None:
    """URL of an already running instance, or None."""
    try:
        port = int(json.loads((data_dir / INSTANCE_FILE).read_text(encoding="utf-8"))["port"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    url = f"http://127.0.0.1:{port}"
    return url if is_healthy(url) else None


def is_healthy(url: str, timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/api/health", timeout=timeout) as response:
            return response.status == 200 and json.load(response) == {"status": "ok"}
    except (OSError, ValueError):
        return False
