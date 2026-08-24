import pytest
import sqlalchemy as sa
from sqlalchemy.orm import clear_mappers, sessionmaker

from asta_la_vista.adapters import orm


@pytest.fixture(scope="session")
def session_factory():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    sa.event.listen(
        engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON")
    )
    orm.start_mappers()
    orm.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    clear_mappers()
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(session_factory):
    with session_factory() as session:
        for table in reversed(orm.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
