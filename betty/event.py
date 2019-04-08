from typing import Callable

POST_PARSE_EVENT = 'parse:post'


class EventDispatcher:
    def __init__(self):
        self._listeners = {}

    def add_listener(self, event_name: str, listener: Callable):
        self._listeners.setdefault(event_name, [])
        self._listeners[event_name].append(listener)

    def dispatch(self, event_name, *args, **kwargs):
        if event_name not in self._listeners:
            return
        for listener in self._listeners[event_name]:
            listener(*args, **kwargs)
