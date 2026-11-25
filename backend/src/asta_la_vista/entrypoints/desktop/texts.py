"""The texts shown outside the page, in the language of the operating system.

They do not follow the language chosen in the page, which is stored in the web view.
"""

import sys

TEXTS = {
    "en": {
        "open_data_folder": "Open Data Folder",
        "missing_web_engine": (
            "Asta la Vista needs Microsoft Edge WebView2, which is not installed on this PC.\n\n"
            "Download it from developer.microsoft.com/microsoft-edge/webview2 "
            "and reopen the app."
        ),
        "startup_failed": (
            "Asta la Vista could not start.\n\nSee the log file for details:\n{log_file}"
        ),
        "older_version_open": (
            "Version {running_version} of Asta la Vista is still open.\n\n"
            "Close it and reopen the app to use version {version}."
        ),
    },
    "it": {
        "open_data_folder": "Apri cartella dati",
        "missing_web_engine": (
            "Asta la Vista ha bisogno di Microsoft Edge WebView2, che su questo PC manca.\n\n"
            "Scaricalo da developer.microsoft.com/microsoft-edge/webview2 e riapri l'app."
        ),
        "startup_failed": (
            "Non è stato possibile avviare Asta la Vista.\n\n"
            "I dettagli sono nel file di log:\n{log_file}"
        ),
        "older_version_open": (
            "È ancora aperta la versione {running_version} di Asta la Vista.\n\n"
            "Chiudila e riapri l'app per usare la versione {version}."
        ),
    },
}


def text(key: str, **params: object) -> str:
    return TEXTS[system_language()][key].format(**params)


def system_language() -> str:
    """``it`` when the first language of the system is Italian, otherwise ``en``."""
    name = ""
    if sys.platform == "darwin":
        from Foundation import NSLocale  # pyobjc, which pywebview needs on macOS

        name = NSLocale.preferredLanguages()[0]  # e.g. "it-IT"
    elif sys.platform == "win32":
        import ctypes
        import locale

        language_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()  # type: ignore[attr-defined]
        name = locale.windows_locale.get(language_id, "")  # e.g. "it_IT"
    return "it" if name.startswith("it") else "en"
