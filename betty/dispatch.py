from typing import Type, List, Any, Callable

TargetedDispatcher = Callable[[], List[Any]]


class Dispatcher:
    def dispatch(self, target_type: Type, target_method_name: str) -> TargetedDispatcher:
        raise NotImplementedError
