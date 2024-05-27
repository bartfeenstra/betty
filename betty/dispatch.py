"""
Provide the Dispatch API.
"""

from typing import Any, Sequence, Callable, Awaitable

TargetedDispatcher = Callable[..., Awaitable[Sequence[Any]]]


class Dispatcher:
    """
    Dispatch events to handlers.
    """

    def dispatch(self, target_type: type[Any]) -> TargetedDispatcher:
        """
        Dispatch a single target.
        """
        raise NotImplementedError(repr(self))
