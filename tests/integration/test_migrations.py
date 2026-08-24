import sqlalchemy as sa
from alembic import command
from alembic.config import Config


def test_initial_migration_upgrades_and_downgrades_sqlite(tmp_path, monkeypatch):
    database_path = tmp_path / "migration.sqlite3"
    database_uri = f"sqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URI", database_uri)
    alembic_config = Config("alembic.ini")

    command.upgrade(alembic_config, "head")

    engine = sa.create_engine(database_uri)
    assert set(sa.inspect(engine).get_table_names()) == {
        "alembic_version",
        "auction",
        "participant",
        "player",
        "purchase",
        "strategy",
        "strategy_entry",
        "tier",
    }

    command.downgrade(alembic_config, "base")
    assert sa.inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()
