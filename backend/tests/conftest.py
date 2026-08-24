import pytest
import sqlalchemy as sa
from sqlalchemy.orm import clear_mappers, sessionmaker

from asta_la_vista.adapters import orm


@pytest.fixture(scope="session")
def mapped_domain():
    orm.start_mappers()
    yield
    clear_mappers()


@pytest.fixture
def session_factory(mapped_domain):
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    sa.event.listen(
        engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON")
    )
    orm.metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()
