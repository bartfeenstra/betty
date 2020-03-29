from collections import defaultdict
from typing import Callable, Type


class Event:
    pass


class EventDispatcher:
    def __init__(self):
        self._listeners = defaultdict(list)

    def add_listener(self, event_type: Type[Event], listener: Callable):
        self._listeners[event_type].append(listener)

    async def dispatch(self, event: Event):
        event_type = type(event)
        if event_type not in self._listeners:
            return
        for listener in self._listeners[event_type]:
            await listener(event)
