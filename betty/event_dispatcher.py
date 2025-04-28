"""
Provide the Dispatch API.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from collections.abc import Awaitable, Callable, Sequence
from typing import (
    TYPE_CHECKING,
    TypeAlias,
    TypeVar,
    final,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping, MutableSequence


class Event:
    """
    An event that can be dispatched and handled.

    For each unique 'conceptual' event (a thing that happens while using Betty),
    a subclass **MUST** be created for that specific event type. Instances of
    these subclasses are dispatched and handled.
    """


_EventT = TypeVar("_EventT", bound=Event)
EventHandler: TypeAlias = Callable[[_EventT], Awaitable[None]]


class _EventHandlerRegistry:
    """
    Manage event handlers.
    """

    def __init__(self):
        self._handlers: MutableMapping[
            type[Event], MutableSequence[Sequence[EventHandler[Event]]]
        ] = defaultdict(list)

    def add_handler(self, event_type: type[_EventT], *handlers: EventHandler[_EventT]):
        """
        Add a batch of one or more event handlers.

        All handlers of a batch are invoked concurrently.
        """
        self._handlers[event_type].append(
            handlers  # type: ignore[arg-type]
        )

    def add_registry(self, event_handler_registry: EventHandlerRegistry) -> None:
        """
        Add another registry to this one.
        """
        for (
            event_type,
            event_type_handler_batches,
        ) in event_handler_registry.handlers.items():
            for event_type_handler_batch in event_type_handler_batches:
                self.add_handler(event_type, *event_type_handler_batch)


@final
class EventHandlerRegistry(_EventHandlerRegistry):
    """
    Manage event handlers.
    """

    @property
    def handlers(
        self,
    ) -> Mapping[type[Event], Sequence[Sequence[EventHandler[Event]]]]:
        """
        The registered event handlers.
        """
        return self._handlers


@final
class EventDispatcher(_EventHandlerRegistry):
    """
    Dispatch events to event handlers.
    """

    async def dispatch(self, event: Event) -> None:
        """
        Dispatch an event.
        """
        for handler_batch in self._handlers[type(event)]:
            await gather(*(handler(event) for handler in handler_batch))
