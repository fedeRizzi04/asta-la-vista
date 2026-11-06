"""Runs the Flask app with waitress on a local port, in a background thread."""

import socket
import sys
import threading

from flask import Flask
from waitress import wasyncore
from waitress.server import create_server

HOST = "127.0.0.1"
# A fixed, uncommon port keeps the page origin stable between launches, so what the window's web
# view remembers (theme, dismissed notices) survives a restart: localStorage belongs to the
# origin, port included. 5000 is avoided on purpose: macOS uses it for AirPlay Receiver.
PREFERRED_PORT = 47615


def bind_socket(preferred_port: int = PREFERRED_PORT) -> socket.socket:
    """Listen on the preferred port, or on any free port if it is taken."""
    try:
        return _bind(preferred_port)
    except OSError:
        return _bind(0)


def _bind(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if sys.platform == "win32":
            # Without this, Windows lets two processes bind the same port.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            # Lets a restart reuse the port while connections of the previous run are still in
            # TIME_WAIT; a port with a live listener stays unavailable.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, port))
    except OSError:
        sock.close()
        raise
    return sock


class BackgroundServer:
    """waitress in a background thread, stoppable from any other thread.

    waitress' own ``run()`` loops forever; closing its sockets from another thread breaks its
    ``select()`` call. Here the loop runs in short slices and checks a stop flag, so the sockets
    are closed by the same thread that polls them.
    """

    def __init__(self, app: Flask, sock: socket.socket) -> None:
        self.port: int = sock.getsockname()[1]
        self.url = f"http://{HOST}:{self.port}"
        # Our own channel map: the loop below polls it and close_all() empties it.
        self._map: dict = {}
        self._server = create_server(app, map=self._map, sockets=[sock], threads=8)
        self._stopping = threading.Event()
        self._thread = threading.Thread(target=self._serve, name="waitress", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stopping.set()
        self._thread.join(timeout=10)

    def _serve(self) -> None:
        try:
            while not self._stopping.is_set():
                wasyncore.loop(timeout=0.2, map=self._map, count=1)
        finally:
            self._server.task_dispatcher.shutdown()
            wasyncore.close_all(self._map)
