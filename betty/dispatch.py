from typing import Callable, Type, List, Any


class TargetedDispatcher:
    def __init__(self, handler_methods):
        self._handler_methods = handler_methods

    async def __call__(self, *args, **kwargs) -> List[Any]:
        return [await handler_method(*args, **kwargs) for handler_method in self._handler_methods]


class Dispatcher:
    def __init__(self):
        self._handlers = []

    def append_handler(self, handler: Callable):
        self._handlers.append(handler)

    def dispatch(self, target_type: Type, target_method_name: str) -> TargetedDispatcher:
        handler_methods = [getattr(handler, target_method_name) for handler in self._handlers if isinstance(handler, target_type)]
        return TargetedDispatcher(handler_methods)
