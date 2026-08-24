from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, event, pool

from asta_la_vista import config as app_config
from asta_la_vista.adapters.orm import metadata

alembic_config = context.config
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)
alembic_config.set_main_option("sqlalchemy.url", app_config.database_uri())


def run_migrations_offline():
    context.configure(
        url=alembic_config.get_main_option("sqlalchemy.url"),
        target_metadata=metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    if connectable.dialect.name == "sqlite":
        event.listen(
            connectable,
            "connect",
            lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
        )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
