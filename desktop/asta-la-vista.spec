# PyInstaller build recipe for the desktop app. Run it through ./bin/build-desktop.
#
# macOS  -> dist/desktop/Asta la Vista.app  (menu-bar app, no Dock icon)
# Windows -> dist/desktop/AstaLaVista.exe   (single file, no console window)
#
# ruff: noqa: F821  (Analysis, PYZ, EXE, COLLECT, BUNDLE and SPECPATH are provided by PyInstaller)

import os
import sys
from importlib.metadata import version
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

from asta_la_vista.entrypoints.desktop import icon

ROOT = Path(SPECPATH).parent
BACKEND = ROOT / "backend"
FRONTEND_BUILD = Path(os.environ.get("ASTA_FRONTEND_BUILD", ROOT / "frontend" / "build"))
VERSION = version("asta-la-vista")

if not (FRONTEND_BUILD / "index.html").is_file():
    raise SystemExit(f"Frontend build not found in {FRONTEND_BUILD}: run `npm run build` first.")

# The icon is drawn in code; PyInstaller converts the PNG to .icns / .ico with Pillow.
ICON = ROOT / "build" / "desktop" / "icon.png"
ICON.parent.mkdir(parents=True, exist_ok=True)
icon.render(1024).save(ICON)

datas = [
    (str(FRONTEND_BUILD), "frontend"),
    (str(BACKEND / "migrations"), "migrations"),
    *collect_data_files("asta_la_vista"),  # e.g. the HTML auction report template
    *collect_data_files("flask_smorest"),
    *copy_metadata("asta-la-vista"),  # importlib.metadata.version() reads it at runtime
]

hiddenimports = [
    # migrations/env.py and the revision files are loaded by Alembic at runtime, so PyInstaller
    # cannot see what they import.
    *collect_submodules("alembic", filter=lambda name: not name.startswith("alembic.testing")),
    "logging.config",
]

a = Analysis(
    [str(ROOT / "desktop" / "launcher.py")],
    pathex=[str(BACKEND / "src")],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest", "tkinter"],
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,
        name="AstaLaVista",
        console=False,
        icon=str(ICON),
    )
    app_dir = COLLECT(exe, a.binaries, a.datas, name="AstaLaVista")
    BUNDLE(
        app_dir,
        name="Asta la Vista.app",
        icon=str(ICON),
        bundle_identifier="io.github.federizzi04.astalavista",
        version=VERSION,
        info_plist={
            "CFBundleDisplayName": "Asta la Vista",
            "CFBundleShortVersionString": VERSION,
            "LSUIElement": True,  # lives in the menu bar only, like the Windows tray icon
            "NSHighResolutionCapable": True,
        },
    )
else:
    EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        name="AstaLaVista",
        console=False,
        icon=str(ICON),
    )
