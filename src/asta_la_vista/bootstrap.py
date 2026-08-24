import functools
import inspect

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from asta_la_vista import config
from asta_la_vista.adapters import orm
from asta_la_vista.service_layer import handlers
from asta_la_vista.service_layer.messagebus import MessageBus
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork, SqlAlchemyUnitOfWork


def bootstrap(uow: AbstractUnitOfWork | None = None) -> MessageBus:
    orm.start_mappers()
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


def _default_uow() -> SqlAlchemyUnitOfWork:
    engine = sa.create_engine(config.database_uri())
    if engine.dialect.name == "sqlite":
        sa.event.listen(
            engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON")
        )
    return SqlAlchemyUnitOfWork(sessionmaker(bind=engine))
