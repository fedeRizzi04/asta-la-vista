import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from unittest.mock import Mock

import pytest

pytest.importorskip("waitress", reason="needs the desktop dependency group")

from asta_la_vista.entrypoints.desktop import app as desktop_app  # noqa: E402
from asta_la_vista.entrypoints.desktop import icon, instance, paths, server  # noqa: E402


def test_data_dir_can_be_overridden(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV, str(tmp_path / "custom"))

    assert paths.data_dir() == tmp_path / "custom"


@pytest.mark.parametrize(
    ("platform", "expected"),
    [
        ("darwin", Path("home") / "Library" / "Application Support" / "Asta la Vista"),
        ("win32", Path("roaming") / "Asta la Vista"),
        ("linux", Path("home") / ".local" / "share" / "asta-la-vista"),
    ],
)
def test_data_dir_follows_platform_conventions(tmp_path, monkeypatch, platform, expected):
    monkeypatch.delenv(paths.DATA_DIR_ENV, raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setattr(paths.Path, "home", lambda: tmp_path / "home")
    monkeypatch.setattr(paths.sys, "platform", platform)

    assert paths.data_dir() == tmp_path / expected


def test_checkout_resources_point_into_the_repository():
    repository = Path(__file__).resolve().parents[3]

    assert paths.migrations_dir() == repository / "backend" / "migrations"
    assert paths.frontend_dist() == repository / "frontend" / "build"


def test_environment_defaults_keep_values_already_set(tmp_path, monkeypatch):
    for name in ("DATABASE_URI", "FRONTEND_DIST", "API_TITLE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("API_TITLE", "Custom")

    desktop_app.configure_environment(tmp_path / "data dir")

    assert os.environ["DATABASE_URI"] == (
        f"sqlite:///{(tmp_path / 'data dir' / 'asta-la-vista.sqlite3').as_posix()}"
    )
    assert os.environ["FRONTEND_DIST"] == str(paths.frontend_dist())
    assert os.environ["API_TITLE"] == "Custom"


def test_bind_socket_falls_back_to_a_free_port_when_the_preferred_one_is_taken():
    with socket.socket() as occupied:
        occupied.bind((server.HOST, 0))
        occupied.listen()
        taken_port = occupied.getsockname()[1]

        sock = server.bind_socket(taken_port)

    try:
        assert sock.getsockname()[1] not in (0, taken_port)
    finally:
        sock.close()


def test_running_url_is_none_without_a_live_instance(tmp_path):
    assert instance.running_url(tmp_path) is None

    instance.write(tmp_path, 9)  # nothing listens on the discard port
    assert instance.running_url(tmp_path) is None

    (tmp_path / instance.INSTANCE_FILE).write_text("not json")
    assert instance.running_url(tmp_path) is None


def test_background_server_serves_the_app_and_is_found_as_running_instance(tmp_path):
    from asta_la_vista.entrypoints.flask_app import create_app
    from asta_la_vista.service_layer.messagebus import MessageBus

    flask_app = create_app(
        {"TESTING": True, "API_TITLE": "T", "API_VERSION": "v1", "OPENAPI_VERSION": "3.1.0"},
        message_bus_factory=lambda: Mock(spec=MessageBus),
    )
    background = server.BackgroundServer(flask_app, server.bind_socket(0))
    background.start()
    try:
        instance.write(tmp_path, background.port)
        deadline = time.monotonic() + 5
        while instance.running_url(tmp_path) is None and time.monotonic() < deadline:
            time.sleep(0.05)

        assert instance.running_url(tmp_path) == background.url
    finally:
        background.stop()
        instance.clear(tmp_path)

    assert not (tmp_path / instance.INSTANCE_FILE).exists()


def test_icon_renders_requested_size():
    pytest.importorskip("PIL")

    image = icon.render(32)

    assert image.size == (32, 32)
    assert image.mode == "RGBA"


def test_instance_lock_is_exclusive_until_released(tmp_path):
    first = instance.acquire_lock(tmp_path)
    assert first is not None
    assert instance.acquire_lock(tmp_path) is None

    first.release()
    second = instance.acquire_lock(tmp_path)
    assert second is not None
    second.release()


def test_restart_gets_the_same_port_while_old_connections_are_in_time_wait():
    from asta_la_vista.entrypoints.flask_app import create_app
    from asta_la_vista.service_layer.messagebus import MessageBus

    flask_app = create_app(
        {"TESTING": True, "API_TITLE": "T", "API_VERSION": "v1", "OPENAPI_VERSION": "3.1.0"},
        message_bus_factory=lambda: Mock(spec=MessageBus),
    )
    background = server.BackgroundServer(flask_app, server.bind_socket(0))
    background.start()
    # Like a browser: a keep-alive connection still open when the app quits, so the server
    # closes it first and the port is left with connections in TIME_WAIT.
    connection = http.client.HTTPConnection(server.HOST, background.port, timeout=5)
    connection.request("GET", "/api/health")
    connection.getresponse().read()
    background.stop()
    connection.close()

    sock = server.bind_socket(background.port)
    try:
        assert sock.getsockname()[1] == background.port
    finally:
        sock.close()


def _launch(data_dir: Path, frontend: Path) -> subprocess.Popen:
    environment = {
        **os.environ,
        paths.DATA_DIR_ENV: str(data_dir),
        "FRONTEND_DIST": str(frontend),
    }
    for name in ("DATABASE_URI", "APP_HOST", "APP_PORT"):
        environment.pop(name, None)
    return subprocess.Popen(
        [sys.executable, "-m", "asta_la_vista.entrypoints.desktop", "--no-browser", "--no-tray"],
        env=environment,
    )


def _wait_for_port(process: subprocess.Popen, data_dir: Path) -> int:
    instance_file = data_dir / instance.INSTANCE_FILE
    deadline = time.monotonic() + 20
    while not instance_file.exists() and time.monotonic() < deadline:
        assert process.poll() is None, "the launcher exited early"
        time.sleep(0.1)
    return json.loads(instance_file.read_text())["port"]


@pytest.fixture
def frontend(tmp_path):
    folder = tmp_path / "frontend"
    folder.mkdir()
    (folder / "index.html").write_text("<h1>Asta la Vista</h1>")
    return folder


@pytest.mark.skipif(sys.platform == "win32", reason="uses SIGTERM")
def test_simultaneous_launches_start_a_single_server(tmp_path, frontend):
    data_dir = tmp_path / "data"  # fresh: both launches would otherwise race on migrations
    first, second = _launch(data_dir, frontend), _launch(data_dir, frontend)
    try:
        assert second.wait(timeout=30) == 0 or first.wait(timeout=30) == 0
        survivor = first if first.poll() is None else second
        assert survivor.poll() is None, "exactly one launch keeps serving"
        port = _wait_for_port(survivor, data_dir)
        assert instance.is_healthy(f"http://127.0.0.1:{port}")

        survivor.send_signal(signal.SIGTERM)
        assert survivor.wait(timeout=10) == 0
    finally:
        for process in (first, second):
            if process.poll() is None:
                process.kill()
    assert {first.returncode, second.returncode} == {0}


@pytest.mark.skipif(sys.platform == "win32", reason="uses SIGTERM")
def test_launcher_starts_migrates_serves_and_stops_cleanly(tmp_path, frontend):
    data_dir = tmp_path / "data dir"
    process = _launch(data_dir, frontend)
    try:
        instance_file = data_dir / instance.INSTANCE_FILE
        port = _wait_for_port(process, data_dir)

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/version") as response:
            assert "version" in json.load(response)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/players") as response:
            assert b"Asta la Vista" in response.read()

        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=10) == 0
    finally:
        if process.poll() is None:
            process.kill()

    assert (data_dir / "asta-la-vista.sqlite3").is_file()
    assert (data_dir / "asta-la-vista.log").is_file()
    assert not instance_file.exists()
