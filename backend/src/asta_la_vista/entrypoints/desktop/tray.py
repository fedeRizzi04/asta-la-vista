"""Icon in the system tray (Windows) or menu bar (macOS) to reopen or quit the app.

Closing the browser tab does not stop the server; this icon is how the user does it.
"""

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from asta_la_vista.entrypoints.desktop import icon as app_icon
from asta_la_vista.entrypoints.desktop.paths import APP_NAME


def run(open_app: Callable[[], None], data_dir: Path) -> None:
    """Show the icon and block until the user picks "Esci"."""
    import pystray  # imported lazily: it needs a desktop session, which tests and CI lack

    def quit_app(icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(f"Apri {APP_NAME}", lambda: open_app(), default=True),
        pystray.MenuItem("Apri cartella dati", lambda: open_folder(data_dir)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Esci", quit_app),
    )
    pystray.Icon("asta-la-vista", app_icon.render(64), APP_NAME, menu).run()


def open_folder(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)
