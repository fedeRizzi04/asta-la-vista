"""The app's own window: a native web view showing the local server. Closing it quits the app.

pywebview drives the web engine the operating system already has: WebView2 (Edge) on Windows and
WKWebView (Safari) on macOS, so nothing as big as a browser is bundled. It must own the main
thread, which is why the server runs in a background thread.
"""

import os
import subprocess
import sys
from pathlib import Path

from asta_la_vista.entrypoints.desktop.paths import APP_NAME

WIDTH, HEIGHT = 1280, 820
MIN_WIDTH, MIN_HEIGHT = 900, 600
SW_RESTORE = 9  # Windows ShowWindow command

# pywebview's own texts: the closing confirmation, file dialogs and the macOS menus.
LOCALIZATION = {
    "global.quitConfirmation": f"Vuoi chiudere {APP_NAME}?",
    "global.quit": "Chiudi",
    "global.cancel": "Annulla",
    "global.saveFile": "Salva file",
    "cocoa.menu.about": "Informazioni su",
    "cocoa.menu.services": "Servizi",
    "cocoa.menu.view": "Vista",
    "cocoa.menu.edit": "Modifica",
    "cocoa.menu.hide": "Nascondi",
    "cocoa.menu.hideOthers": "Nascondi altre",
    "cocoa.menu.showAll": "Mostra tutte",
    "cocoa.menu.quit": "Esci da",
    "cocoa.menu.fullscreen": "Attiva modalità a tutto schermo",
    "cocoa.menu.cut": "Taglia",
    "cocoa.menu.copy": "Copia",
    "cocoa.menu.paste": "Incolla",
    "cocoa.menu.selectAll": "Seleziona tutto",
    "windows.fileFilter.allFiles": "Tutti i file",
    "windows.fileFilter.otherFiles": "Altri tipi di file",
}


class MissingWebEngine(RuntimeError):
    """Windows without the WebView2 runtime: pywebview would fall back to Internet Explorer."""

    def __init__(self) -> None:
        super().__init__(
            f"{APP_NAME} ha bisogno di Microsoft Edge WebView2, che su questo PC manca.\n\n"
            "Scaricalo da developer.microsoft.com/microsoft-edge/webview2 e riapri l'app."
        )


def run(url: str, data_dir: Path) -> None:
    """Open the window on ``url`` and block until the user closes it."""
    import webview  # imported lazily: it needs a desktop session, which tests and CI lack
    from webview.menu import Menu, MenuAction

    _require_modern_engine()
    # Off by default in pywebview; the report and strategy exports are downloads.
    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.create_window(
        APP_NAME,
        url,
        width=WIDTH,
        height=HEIGHT,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        confirm_close=True,  # closing quits the app: ask first, an auction may be in progress
        menu=[Menu("File", [MenuAction("Apri cartella dati", lambda: open_folder(data_dir))])],
    )
    webview.start(
        # pywebview's default private mode forgets localStorage (theme, dismissed banner) at
        # every launch, and on macOS even clears the data saved by earlier launches.
        private_mode=False,
        # Used on Windows only; macOS keeps it in ~/Library/WebKit and ~/Library/Caches.
        storage_path=str(data_dir / "webview"),
        localization=LOCALIZATION,
    )


def bring_to_front() -> None:
    """Show the window of the copy already running, for a second double-click on Windows.

    macOS needs nothing: it never starts a second copy of an open app, it activates the first.
    """
    if sys.platform != "win32":
        return
    import ctypes

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    handle = user32.FindWindowW(None, APP_NAME)  # pywebview keeps the title, whatever the page
    if not handle:
        return
    if user32.IsIconic(handle):  # minimised; restoring a visible window would un-maximise it
        user32.ShowWindow(handle, SW_RESTORE)
    user32.SetForegroundWindow(handle)


def _require_modern_engine() -> None:
    if sys.platform != "win32":
        return
    from webview.platforms import winforms

    if winforms.renderer != "edgechromium":
        raise MissingWebEngine


def open_folder(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)
