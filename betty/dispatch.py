"""
Provide the Dispatch API.
"""

from abc import ABC, abstractmethod
from typing import Any, Sequence, Callable, Awaitable

TargetedDispatcher = Callable[..., Awaitable[Sequence[Any]]]


class Dispatcher(ABC):
    """
    Dispatch events to handlers.
    """

    @abstractmethod
    def dispatch(self, target_type: type[Any]) -> TargetedDispatcher:
        """
        Dispatch a single target.
        """
        pass
