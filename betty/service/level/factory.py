"""
Service level factories.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, Self, TypeAlias

from typing_extensions import TypeVar

from betty.factory import Target

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel

_T = TypeVar("_T")


class ServiceLevelDependentSelfFactory(ABC):
    """
    Allow this type to be instantiated using a :py:class:`betty.service.level.ServiceLevel`.
    """

    @classmethod
    @abstractmethod
    async def new_for_services(cls, *, services: ServiceLevel) -> Self:
        """
        Create a new instance using the given service level.
        """


ServiceLevelTarget: TypeAlias = ServiceLevelDependentSelfFactory | Target[_T]
"""
#. If ``target`` subclasses :py:class:`betty.service.factory.ServiceLevelDependentSelfFactory`, this will return 
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
