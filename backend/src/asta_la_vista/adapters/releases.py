"""Finds out whether a newer version of the app has been published on GitHub.

Only the desktop app checks by default: Docker and development setups opt in with
``UPDATE_CHECK=true``. Being offline, or GitHub being slow, never disturbs the app: the check
runs in a background thread, the caller waits for it only briefly, and failures are just logged.
"""

import json
import logging
import re
import threading
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from asta_la_vista import __version__

REPOSITORY = "fedeRizzi04/asta-la-vista"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPOSITORY}/releases/"
REQUEST_TIMEOUT = 5.0
# GitHub allows 60 anonymous API requests per hour and releases are rare: ask a few times a day.
RECHECK_AFTER_SUCCESS = 6 * 60 * 60.0
# After a failure (usually: offline) retry soon, so a reconnection is noticed quickly. GitHub is
# asked only when the page asks the server, at most every minute or so, well within the limit.
RECHECK_AFTER_FAILURE = 60.0

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Release:
    version: str
    url: str


def fetch_latest_release() -> Release:
    """Ask GitHub for the latest published release (drafts and pre-releases are excluded)."""
    request = urllib.request.Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"asta-la-vista/{__version__}",
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        payload = json.load(response)

    version = str(payload["tag_name"]).removeprefix("v")
    url = str(payload["html_url"])
    if parse_version(version) is None:
        raise ValueError(f"Unexpected release tag: {payload['tag_name']!r}")
    # The page links to this URL: accept only release pages of this repository.
    if not url.startswith(RELEASES_PAGE):
        raise ValueError(f"Unexpected release URL: {url!r}")
    return Release(version=version, url=url)


def parse_version(version: str) -> tuple[int, int, int] | None:
    """``"1.2.3"`` → ``(1, 2, 3)``; anything else (``"1.2"``, ``"1.2.3rc1"``) → ``None``."""
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def is_newer(candidate: str, current: str) -> bool:
    candidate_parts = parse_version(candidate)
    # A local build such as "0.2.0+dirty" still compares as 0.2.0.
    current_parts = parse_version(current.split("+", 1)[0])
    if candidate_parts is None or current_parts is None:
        return False
    return candidate_parts > current_parts


class ReleaseChecker:
    """Remembers the latest release and refreshes it in the background when it gets old."""

    def __init__(
        self,
        fetch: Callable[[], Release] = fetch_latest_release,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fetch = fetch
        self._clock = clock
        self._lock = threading.Lock()
        self._latest: Release | None = None
        self._next_check_at = 0.0
        self._pending: threading.Thread | None = None

    def latest(self, wait: float) -> Release | None:
        """Return the latest known release, waiting at most ``wait`` seconds for a refresh.

        A refresh still running when the wait ends keeps going and serves later calls.
        """
        with self._lock:
            if self._pending is None and self._clock() >= self._next_check_at:
                self._pending = threading.Thread(
                    target=self._refresh, name="release-check", daemon=True
                )
                self._pending.start()
            pending = self._pending
        if pending is not None:
            pending.join(wait)
        with self._lock:
            return self._latest

    def _refresh(self) -> None:
        try:
            release = self._fetch()
        except Exception as error:  # offline, timeout, rate limit, unexpected answer...
            log.info("Could not check for updates: %s", error)
            with self._lock:
                self._next_check_at = self._clock() + RECHECK_AFTER_FAILURE
                self._pending = None
            return
        with self._lock:
            self._latest = release
            self._next_check_at = self._clock() + RECHECK_AFTER_SUCCESS
            self._pending = None
