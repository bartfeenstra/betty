from typing import Type, Any, Sequence, Callable, Awaitable

TargetedDispatcher = Callable[..., Awaitable[Sequence[Any]]]


class Dispatcher:
    def dispatch(self, target_type: Type, target_method_name: str) -> TargetedDispatcher:
        raise NotImplementedError
