"""
Object factories.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Self, overload

from betty.call import Arg1Callback, Arg2Callback, Callback, call


class Manufacturable(metaclass=ABCMeta):
    """
    Allow this type to be initialized asynchronously.
    """

    @classmethod
    @abstractmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """


class Arg1Manufacturable[Arg1T](metaclass=ABCMeta):
    """
    Allow this type to be initialized using a argument.
    """

    @classmethod
    @abstractmethod
    async def new(cls, arg1: Arg1T, /) -> Self:
        """
        Create a new instance.
        """


class Arg2Manufacturable[Arg1T, Arg2T](metaclass=ABCMeta):
    """
    Allow this type to be initialized using two arguments.
    """

    @classmethod
    @abstractmethod
    async def new(cls, arg1: Arg1T, arg2: Arg2T, /) -> Self:
        """
        Create a new instance.
        """


type Manufacturer[T] = type[Manufacturable] | Callback[T]


type Arg1Manufacturer[T, Arg1T] = (
    type[Arg1Manufacturable[Arg1T]] | Arg1Callback[T, Arg1T]
)


type Arg2Manufacturer[T, Arg1T, Arg2T] = (
    type[Arg2Manufacturable[Arg1T, Arg2T]] | Arg2Callback[T, Arg1T, Arg2T]
)


@overload
async def new[T](manufacturer: Manufacturer[T], /) -> T:
    pass


@overload
async def new[T, Arg1T](manufacturer: Arg1Manufacturer[T, Arg1T], arg1: Arg1T, /) -> T:
    pass


@overload
async def new[T, Arg1T, Arg2T](
    manufacturer: Arg2Manufacturer[T, Arg1T, Arg2T], arg1: Arg1T, arg2: Arg2T, /
) -> T:
    pass


async def new(manufacturer, *args):
    """
    Create a new object from a manufacturer.
    """
    if isinstance(manufacturer, type):
        for manufacturable_cls in (
            Arg2Manufacturable,
            Arg1Manufacturable,
            Manufacturable,
        ):
            if issubclass(manufacturer, manufacturable_cls):
                manufacturer = manufacturer.new
                break
    return await call(manufacturer, *args)
