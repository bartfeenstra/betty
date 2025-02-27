"""
Functionality for creating new instances of types that depend on :py:class:`betty.app.App`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self, TYPE_CHECKING, TypeVar, Generic

if TYPE_CHECKING:
    from betty.app import App

_TargetT = TypeVar("_TargetT")


class AppDependentFactory(ABC):
    """
    Allow this type to be instantiated using a :py:class:`betty.app.App`.
    """

    @classmethod
    @abstractmethod
    async def new_for_app(cls, app: App) -> Self:
        """
        Create a new instance using the given app.
        """
        pass


class AppDependentTargetFactory(Generic[_TargetT], ABC):
    """
    Allow this type to be instantiated using a :py:class:`betty.app.App`.
    """

    @abstractmethod
    async def new_for_app(self, app: App) -> _TargetT:
        """
        Create a new instance using the given app.
        """
        pass
