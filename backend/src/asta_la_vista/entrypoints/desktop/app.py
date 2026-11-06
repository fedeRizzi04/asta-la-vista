"""Desktop entry point: prepares the data folder, starts the server, opens the browser."""

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
import webbrowser
from logging.handlers import RotatingFileHandler
from pathlib import Path

from asta_la_vista.entrypoints.desktop import instance, paths
from asta_la_vista.entrypoints.desktop.paths import APP_NAME
from asta_la_vista.entrypoints.desktop.server import PREFERRED_PORT

DATABASE_FILE = "asta-la-vista.sqlite3"
LOG_FILE = "asta-la-vista.log"

log = logging.getLogger("asta_la_vista.desktop")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _ensure_standard_streams()
    data_dir = paths.data_dir()
    data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    _configure_logging(data_dir)

    try:
        return _run(args, data_dir)
    except Exception:
        log.exception("Asta la Vista could not start")
        if paths.is_frozen() and not args.no_tray:
            _show_error(
                f"Non è stato possibile avviare {APP_NAME}.\n\n"
                f"I dettagli sono nel file di log:\n{data_dir / LOG_FILE}"
            )
        return 1


def _run(args: argparse.Namespace, data_dir: Path) -> int:
    running = instance.running_url(data_dir)
    if running:
        log.info("Already running at %s, opening the browser", running)
        if not args.no_browser:
            webbrowser.open(running)
        return 0

    configure_environment(data_dir)

    # Imported here, after the environment is set, because they read the configuration.
    from asta_la_vista.adapters.migrations import upgrade_database
    from asta_la_vista.entrypoints.desktop import server as desktop_server
    from asta_la_vista.entrypoints.flask_app import create_app

    log.info("Starting %s, data folder: %s", APP_NAME, data_dir)
    upgrade_database(paths.migrations_dir())
    server = desktop_server.BackgroundServer(create_app(), desktop_server.bind_socket(args.port))
    server.start()
    try:
        _wait_until_healthy(server.url)
        instance.write(data_dir, server.port)
        log.info("Serving on %s", server.url)

        def open_app() -> None:
            webbrowser.open(server.url)

        if not args.no_browser:
            open_app()
        if args.no_tray:
            _wait_for_termination()
        else:
            from asta_la_vista.entrypoints.desktop import tray

            tray.run(open_app, data_dir)
    finally:
        instance.clear(data_dir)
        server.stop()
        log.info("Stopped")
    return 0


def configure_environment(data_dir: Path) -> None:
    """Provide the settings that Docker and ``backend/.env`` provide in the other setups.

    ``setdefault`` keeps any value already exported, which is handy for debugging.
    """
    defaults = {
        "DATABASE_URI": f"sqlite:///{(data_dir / DATABASE_FILE).as_posix()}",
        "FRONTEND_DIST": str(paths.frontend_dist()),
        "APP_HOST": "127.0.0.1",
        "APP_PORT": "0",  # required by the settings loader; the launcher picks the real port
        "API_TITLE": "Asta la Vista API",
        "API_VERSION": "v1",
        "OPENAPI_VERSION": "3.1.0",
    }
    for name, value in defaults.items():
        os.environ.setdefault(name, value)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="asta-la-vista", description=f"Avvia {APP_NAME}.")
    parser.add_argument("--port", type=int, default=PREFERRED_PORT, help="porta preferita")
    parser.add_argument("--no-browser", action="store_true", help="non aprire il browser")
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="niente icona di sistema: resta in esecuzione fino a Ctrl+C (per test e CI)",
    )
    # macOS may append a "-psn_..." argument when launching an app bundle; ignore unknown ones.
    args, _unknown = parser.parse_known_args(argv)
    return args


def _ensure_standard_streams() -> None:
    # Windowed executables have no console: sys.stdout/stderr are None and any print would fail.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")  # noqa: SIM115
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")  # noqa: SIM115


def _configure_logging(data_dir: Path) -> None:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = RotatingFileHandler(
        data_dir / LOG_FILE, maxBytes=1_000_000, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers[:] = [file_handler, console_handler]


def _wait_until_healthy(url: str, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if instance.is_healthy(url):
            return
        time.sleep(0.1)
    raise RuntimeError(f"The server did not answer on {url} within {timeout:.0f}s")


def _wait_for_termination() -> None:
    # SIGTERM is turned into KeyboardInterrupt, like Ctrl+C. The handler must not touch locks
    # (e.g. threading.Event.set): it runs on the main thread, possibly while that thread holds them.
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    try:
        while True:
            time.sleep(0.5)  # short sleeps keep Ctrl+C responsive on Windows
    except KeyboardInterrupt:
        pass


def _show_error(message: str) -> None:
    try:
        if sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x10)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            escaped = message.replace("\\", "\\\\").replace('"', '\\"')
            subprocess.run(
                ["osascript", "-e", f'display alert "{APP_NAME}" message "{escaped}" as critical'],
                check=False,
            )
    except Exception:
        log.exception("Could not show the error dialog")
