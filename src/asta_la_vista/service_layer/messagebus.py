import logging
from collections import deque
from collections.abc import Callable
from typing import Any

from asta_la_vista.domain import commands, events
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)
CommandHandler = Callable[[commands.Command], Any]
EventHandler = Callable[[events.Event], Any]


class MessageBus:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        event_handlers: dict[type[events.Event], list[EventHandler]],
        command_handlers: dict[type[commands.Command], CommandHandler],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.queue: deque[commands.Command | events.Event] = deque()

    def handle(self, message: commands.Command | events.Event):
        self.queue.append(message)
        result = None
        while self.queue:
            current = self.queue.popleft()
            if isinstance(current, events.Event):
                self._handle_event(current)
            elif isinstance(current, commands.Command):
                result = self._handle_command(current)
            else:
                raise TypeError(f"Unsupported message: {type(current)!r}")
        return result

    def _handle_command(self, command: commands.Command):
        handler = self.command_handlers[type(command)]
        result = handler(command)
        self.queue.extend(self.uow.collect_new_events())
        return result

    def _handle_event(self, event: events.Event):
        for handler in self.event_handlers.get(type(event), []):
            try:
                handler(event)
                self.queue.extend(self.uow.collect_new_events())
            except Exception:
                logger.exception("Event handler failed for %r", event)
