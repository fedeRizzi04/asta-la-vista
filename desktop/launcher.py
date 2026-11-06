"""Entry script for PyInstaller (it needs a file, not a ``-m`` module)."""

from asta_la_vista.entrypoints.desktop.app import main

raise SystemExit(main())
