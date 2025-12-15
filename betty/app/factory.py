"""
Functionality for creating new instances of types that depend on :py:class:`betty.app.App`.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Generic,
    Self,
    TypeAlias,
    TypeVar,
    final,
)

from typing_extensions import override

from betty.asyncio import ensure_await
from betty.factory import Target
from betty.requirement import HasRequirement, Requirement

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.app import App
    from betty.service.level import ServiceLevel


_T = TypeVar("_T")


class AppDependentSelfFactory(HasRequirement):
    """
    Allow this type to be instantiated using a :py:class:`betty.app.App`.
    """

    @classmethod
    @abstractmethod
    async def new_for_app(cls, app: App, /) -> Self:
        """
        Create a new instance using the given app.
        """

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        from betty.app import App

        return await App.requirement_for(services, str(cls))


class AppDependentFactory(Generic[_T]):
    """
    Create new instances using a :py:class:`betty.app.App`.
    """

    @abstractmethod
    async def new_for_app(self, app: App, /) -> _T:
        """
        Create a new instance using the given app.
        """


@final
class CallbackAppDependentFactory(AppDependentFactory[_T], Generic[_T]):
    """
    Create new instances using a callback that takes a :py:class:`betty.app.App`.
    """

    def __init__(
        self, callback: Callable[[App], Awaitable[_T]] | Callable[[App], _T], /
    ):
        self._callback = callback

    @override
    async def new_for_app(self, app: App, /) -> _T:
        return await ensure_await(self._callback(app))


AppTarget: TypeAlias = Target[_T] | AppDependentSelfFactory | AppDependentFactory[_T]
"""
#. If ``target`` subclasses :py:class:`betty.app.factory.AppDependentSelfFactory`, this will return ``target``'s
   ``new_for_app()``'s return value.
#. If ``target`` is an instance of :py:class:`betty.app.factory.AppDependentFactory`, this will return ``target``'s
   ``new_for_app()``'s return value.
#. Else, ``target`` will be treated as :py:type:`betty.factory.Target`.
"""
