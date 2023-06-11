from typing import Any, Sequence, Callable, Awaitable

TargetedDispatcher = Callable[..., Awaitable[Sequence[Any]]]


class Dispatcher:
    def dispatch(self, target_type: type[Any]) -> TargetedDispatcher:
        raise NotImplementedError(repr(self))
