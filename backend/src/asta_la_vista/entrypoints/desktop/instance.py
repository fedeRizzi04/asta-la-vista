"""Keeps a single copy of the app running.

The first launch takes an exclusive lock on ``instance.lock`` in the data folder, before touching
the database, and keeps it until it quits; the operating system releases it even after a crash.
Once its server answers, it writes the port to ``instance.json``. A later launch that cannot get
the lock waits for that file to point at a live server and then just opens the browser on it.
"""

import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import IO

INSTANCE_FILE = "instance.json"
LOCK_FILE = "instance.lock"


class InstanceLock:
    def __init__(self, handle: IO[str]) -> None:
        self._handle = handle

    def release(self) -> None:
        _unlock(self._handle)
        self._handle.close()


def acquire_lock(data_dir: Path) -> InstanceLock | None:
    """Take the single-instance lock, or return None if another launch holds it."""
    handle = open(data_dir / LOCK_FILE, "a+")  # noqa: SIM115 - kept open while the app runs
    try:
        _lock(handle)
    except OSError:
        handle.close()
        return None
    return InstanceLock(handle)


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


def wait_for_running_url(data_dir: Path, timeout: float) -> str | None:
    """Wait for the instance holding the lock to finish starting (e.g. running migrations)."""
    deadline = time.monotonic() + timeout
    while True:
        url = running_url(data_dir)
        if url or time.monotonic() >= deadline:
            return url
        time.sleep(0.2)


def is_healthy(url: str, timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/api/health", timeout=timeout) as response:
            return response.status == 200 and json.load(response) == {"status": "ok"}
    except (OSError, ValueError):
        return False


if sys.platform == "win32":
    import msvcrt

    def _lock(handle: IO[str]) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)

    def _unlock(handle: IO[str]) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _lock(handle: IO[str]) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(handle: IO[str]) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
