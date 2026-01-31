"""
Service level factories.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, Protocol, Self, TypeAlias, final, overload

from typing_extensions import TypeVar, override

from betty.asyncio import resolve_await
from betty.factory import Target

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.service.level import ServiceLevel

_T = TypeVar("_T")


class ServiceLevelDependentFactory(Generic[_T]):
    """
    Create new instances using a :py:class:`betty.service.level.ServiceLevel`.
    """

    @abstractmethod
    async def new_for_services(self, services: ServiceLevel, /) -> _T:
        """
        Create a new instance using the given service level.
        """


class ServiceLevelDependentSelfFactory:
    """
    Allow this type to be instantiated using a :py:class:`betty.service.level.ServiceLevel`.
    """

    @classmethod
    @abstractmethod
    async def new_for_services(cls, services: ServiceLevel, /) -> Self:
        """
        Create a new instance using the given service level.
        """


@final
class CallbackServiceLevelDependentFactory(ServiceLevelDependentFactory[_T]):
    """
    Create new instances using a callback that takes a :py:class:`betty.service.level.ServiceLevel`.
    """

    @overload
    def __init__(
        self,
        callback: Callable[[ServiceLevel], Awaitable[_T]],
        /,
    ):
        pass

    @overload
    def __init__(
        self,
        callback: Callable[[ServiceLevel], _T],
        /,
    ):
        pass

    def __init__(
        self,
        callback,
        /,
    ):
        self._callback = callback

    @override
    async def new_for_services(self, services: ServiceLevel, /) -> _T:
        return await resolve_await(self._callback(services))


ServiceLevelTarget: TypeAlias = (
    ServiceLevelDependentFactory[_T] | ServiceLevelDependentSelfFactory | Target[_T]
)
"""
#. If ``target`` subclasses :py:class:`betty.service.factory.ServiceLevelDependentSelfFactory`, this will return 
   ``target``'s ``new_for_services()``'s return value.
#. If ``target`` is an instance of :py:class:`betty.service.factory.ServiceLevelDependentFactory`, this will return
   ``target``'s ``new_for_services()``'s return value.
#. Else, ``target`` will be treated as :py:type:`betty.factory.Target`.
"""


class ServiceLevelFactory(Protocol):
    """
    A factory for service level targets.
    """

    async def __call__(self, target: ServiceLevelTarget[_T], /) -> _T:
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be instantiated.
        """
