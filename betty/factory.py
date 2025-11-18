"""
Functionality for creating new class instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, Self, TypeVar, cast


class FactoryError(RuntimeError):
    """
    Raised when a class could not be instantiated by a factory API.
    """

    def __init__(self, new_cls: type, /):
        super().__init__(f"Could not instantiate {new_cls}")


class IndependentFactory(ABC):
    """
    Provide a factory for classes that can instantiate themselves asynchronously.
    """

    @classmethod
    @abstractmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """


_T = TypeVar("_T")


async def new(cls: type[_T]) -> _T:
    """
    Create a new instance.

    :return:
            #. If ``cls`` extends :py:class:`betty.factory.IndependentFactory`, this will call return ``cls``'s
                ``new()``'s return value.
            #. Otherwise ``cls()`` will be called without arguments, and the resulting instance will be returned.

    :raises FactoryError: raised when ``cls`` could not be instantiated.
    """
    if issubclass(cls, IndependentFactory):
        return cast(_T, await cls.new())
    try:
        return cls()
    except Exception as error:
        raise FactoryError(cls) from error


class TargetFactory(ABC):
    """
    Provide a factory for classes that depend on ``self``.
    """

    @abstractmethod
    async def new_target(self, cls: type[_T]) -> _T:
        """
        Create a new instance.

        :raises FactoryError: raised when ``cls`` could not be instantiated.
        """


class Factory(Protocol):
    """
    A callable to create a new instance.
    """

    async def __call__(self, cls: type[_T]) -> _T:
        """
        Create a new instance.

        :raises FactoryError: raised when ``cls`` could not be instantiated.
        """
