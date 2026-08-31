import functools
import inspect
from collections.abc import Callable

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from asta_la_vista import config
from asta_la_vista.service_layer import handlers
from asta_la_vista.service_layer.messagebus import MessageBus
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork, SqlAlchemyUnitOfWork

MessageBusFactory = Callable[[], MessageBus]


def bootstrap(uow: AbstractUnitOfWork | None = None) -> MessageBus:
    uow = uow or _default_uow()
    dependencies = {"uow": uow}

    def inject(handler):
        parameters = inspect.signature(handler).parameters
        return functools.partial(
            handler, **{name: value for name, value in dependencies.items() if name in parameters}
        )

    return MessageBus(
        uow,
        {
            event: [inject(handler) for handler in event_handlers]
            for event, event_handlers in handlers.EVENT_HANDLERS.items()
        },
        {command: inject(handler) for command, handler in handlers.COMMAND_HANDLERS.items()},
    )


def bootstrap_factory() -> MessageBusFactory:
    session_factory = _default_session_factory()
    return lambda: bootstrap(SqlAlchemyUnitOfWork(session_factory))


def _default_uow() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_default_session_factory())


def _default_session_factory() -> sessionmaker[Session]:
    engine = sa.create_engine(config.database_uri())
    if engine.dialect.name == "sqlite":
        sa.event.listen(
            engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON")
        )
    return sessionmaker(bind=engine)
