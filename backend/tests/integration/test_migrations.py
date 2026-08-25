import sqlalchemy as sa
from alembic import command
from alembic.config import Config


def test_initial_migration_upgrades_and_downgrades_sqlite(tmp_path, monkeypatch):
    database_path = tmp_path / "missing" / "migration.sqlite3"
    database_uri = f"sqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URI", database_uri)
    alembic_config = Config("alembic.ini")
    assert not database_path.parent.exists()

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
    assert {column["name"] for column in sa.inspect(engine).get_columns("tier")} == {
        "uuid",
        "strategy_id",
        "name",
        "position",
        "color",
    }
    assert {column["name"] for column in sa.inspect(engine).get_columns("player")} == {
        "external_id",
        "name",
        "team",
        "role",
        "quotation",
        "active",
    }
    assert {column["name"] for column in sa.inspect(engine).get_columns("strategy_entry")} == {
        "uuid",
        "strategy_id",
        "player_id",
        "role",
        "tier_id",
        "note",
        "maximum_price_percentage",
    }

    command.downgrade(alembic_config, "base")
    assert sa.inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()


def test_global_tier_migration_merges_matching_role_tiers(tmp_path, monkeypatch):
    database_path = tmp_path / "migration.sqlite3"
    database_uri = f"sqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URI", database_uri)
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "4bd995617d1c")
    engine = sa.create_engine(database_uri)
    with engine.begin() as connection:
        connection.execute(sa.text("INSERT INTO strategy (uuid, name) VALUES ('strategy', 'Main')"))
        connection.execute(
            sa.text("""
                INSERT INTO player (external_id, name, team, role, active) VALUES
                    ('p1', 'Goalkeeper', 'Roma', 'P', TRUE),
                    ('p2', 'Forward', 'Inter', 'A', TRUE)
            """)
        )
        connection.execute(
            sa.text("""
                INSERT INTO tier (uuid, strategy_id, role, name, position, color) VALUES
                    ('top-p', 'strategy', 'P', 'Top', 0, '#111111'),
                    ('top-a', 'strategy', 'A', 'Top', 0, '#222222'),
                    ('good-a', 'strategy', 'A', 'Good', 1, '#333333')
            """)
        )
        connection.execute(
            sa.text("""
                INSERT INTO strategy_entry
                    (uuid, strategy_id, player_id, role, tier_id, note) VALUES
                    ('entry-p', 'strategy', 'p1', 'P', 'top-p', ''),
                    ('entry-a', 'strategy', 'p2', 'A', 'top-a', '')
            """)
        )

    command.upgrade(alembic_config, "head")

    with engine.connect() as connection:
        tiers = (
            connection.execute(
                sa.text("SELECT uuid, name, position, color FROM tier ORDER BY position")
            )
            .mappings()
            .all()
        )
        entries = (
            connection.execute(
                sa.text("SELECT player_id, tier_id FROM strategy_entry ORDER BY player_id")
            )
            .mappings()
            .all()
        )
    assert [dict(tier) for tier in tiers] == [
        {"uuid": "top-p", "name": "Top", "position": 0, "color": "#111111"},
        {"uuid": "good-a", "name": "Good", "position": 1, "color": "#333333"},
    ]
    assert [dict(entry) for entry in entries] == [
        {"player_id": "p1", "tier_id": "top-p"},
        {"player_id": "p2", "tier_id": "top-p"},
    ]
    assert "maximum_price_percentage" in {
        column["name"] for column in sa.inspect(engine).get_columns("strategy_entry")
    }
    engine.dispose()
