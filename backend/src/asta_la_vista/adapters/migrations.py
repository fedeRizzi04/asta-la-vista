from pathlib import Path

from alembic import command
from alembic.config import Config

from asta_la_vista import config

DEFAULT_SCRIPT_LOCATION = config.BACKEND_ROOT / "migrations"


def upgrade_database(script_location: Path | None = None) -> None:
    """Bring the configured database up to the latest schema.

    Unlike the ``alembic`` CLI, this does not need ``alembic.ini`` or a particular working
    directory, so the desktop build can point it at the migrations bundled inside the executable.
    The database URL is still read from ``DATABASE_URI`` by ``migrations/env.py``.
    """
    alembic_config = Config()
    alembic_config.set_main_option(
        "script_location", str(script_location or DEFAULT_SCRIPT_LOCATION)
    )
    alembic_config.set_main_option("path_separator", "os")
    command.upgrade(alembic_config, "head")
