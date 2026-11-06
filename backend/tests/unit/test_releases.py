import io
import json
import threading

import pytest

from asta_la_vista.adapters import releases
from asta_la_vista.adapters.releases import Release, ReleaseChecker, is_newer, parse_version

RELEASE = Release("0.2.0", "https://github.com/fedeRizzi04/asta-la-vista/releases/tag/v0.2.0")


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.mark.parametrize(
    ("version", "expected"),
    [("0.1.0", (0, 1, 0)), ("12.3.45", (12, 3, 45)), ("1.2", None), ("1.2.3rc1", None), ("", None)],
)
def test_parse_version(version, expected):
    assert parse_version(version) == expected


@pytest.mark.parametrize(
    ("candidate", "current", "expected"),
    [
        ("0.2.0", "0.1.0", True),
        ("0.10.0", "0.9.0", True),  # numeric, not alphabetical
        ("1.0.0", "0.99.99", True),
        ("0.1.0", "0.1.0", False),
        ("0.1.0", "0.2.0", False),
        ("0.2.0", "0.2.0+dirty", False),
        ("0.2.0", "0.0.0+unknown", True),
        ("garbage", "0.1.0", False),
    ],
)
def test_is_newer(candidate, current, expected):
    assert is_newer(candidate, current) is expected


def test_checker_asks_github_once_and_reuses_the_answer():
    calls = []
    clock = FakeClock()
    checker = ReleaseChecker(fetch=lambda: calls.append(1) or RELEASE, clock=clock)

    assert checker.latest(wait=5) == RELEASE
    clock.now += releases.RECHECK_AFTER_SUCCESS - 1
    assert checker.latest(wait=5) == RELEASE

    assert len(calls) == 1


def test_checker_asks_again_once_the_answer_is_old():
    answers = iter([RELEASE, Release("0.3.0", RELEASE.url)])
    clock = FakeClock()
    checker = ReleaseChecker(fetch=lambda: next(answers), clock=clock)

    checker.latest(wait=5)
    clock.now += releases.RECHECK_AFTER_SUCCESS

    assert checker.latest(wait=5) == Release("0.3.0", RELEASE.url)


def test_checker_failure_keeps_the_previous_answer_and_retries_later():
    answers = iter([RELEASE, OSError("offline"), OSError("offline"), Release("0.3.0", RELEASE.url)])

    def fetch() -> Release:
        answer = next(answers)
        if isinstance(answer, Exception):
            raise answer
        return answer

    clock = FakeClock()
    checker = ReleaseChecker(fetch=fetch, clock=clock)
    checker.latest(wait=5)
    clock.now += releases.RECHECK_AFTER_SUCCESS

    assert checker.latest(wait=5) == RELEASE  # offline: still the last known release
    clock.now += releases.RECHECK_AFTER_FAILURE - 1
    assert checker.latest(wait=5) == RELEASE  # not retried yet
    clock.now += 1
    assert checker.latest(wait=5) == RELEASE  # retried, still offline
    clock.now += releases.RECHECK_AFTER_FAILURE
    assert checker.latest(wait=5) == Release("0.3.0", RELEASE.url)


def test_slow_github_does_not_block_and_the_answer_serves_later_calls():
    release_github = threading.Event()
    calls = []

    def slow_fetch() -> Release:
        calls.append(1)
        release_github.wait(5)
        return RELEASE

    checker = ReleaseChecker(fetch=slow_fetch)

    assert checker.latest(wait=0.05) is None
    assert checker.latest(wait=0.05) is None  # the first request is still running
    release_github.set()
    assert checker.latest(wait=5) == RELEASE
    assert len(calls) == 1


def _github_answer(monkeypatch, payload: dict[str, object]) -> list[object]:
    requests = []

    def urlopen(request, timeout):
        requests.append(request)
        return io.BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr(releases.urllib.request, "urlopen", urlopen)
    return requests


def test_fetch_latest_release_reads_the_github_answer(monkeypatch):
    requests = _github_answer(
        monkeypatch, {"tag_name": "v0.2.0", "html_url": RELEASE.url, "draft": False}
    )

    assert releases.fetch_latest_release() == RELEASE
    assert requests[0].full_url == releases.LATEST_RELEASE_API
    assert requests[0].get_header("User-agent").startswith("asta-la-vista/")


@pytest.mark.parametrize(
    "payload",
    [
        {"tag_name": "nightly", "html_url": RELEASE.url},
        {"tag_name": "v0.2.0", "html_url": "https://example.com/malware"},
        {"tag_name": "v0.2.0"},
    ],
)
def test_fetch_latest_release_rejects_unexpected_answers(monkeypatch, payload):
    _github_answer(monkeypatch, payload)

    with pytest.raises((ValueError, KeyError)):
        releases.fetch_latest_release()
