"""
Service level factories.
"""

from typing import Protocol, TypeAlias

from typing_extensions import TypeVar

from betty.project.factory import ProjectTarget

_T = TypeVar("_T")


AnyFactoryTarget: TypeAlias = ProjectTarget[_T]
"""
A factory target for any service level.
"""


class AnyFactory(Protocol):
    """
    A factory for any service level.
    """

    async def __call__(self, target: AnyFactoryTarget[_T], /) -> _T:
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be instantiated.
        """
