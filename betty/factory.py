"""
The factory API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from typing import Self

from ty_extensions import Intersection


class Manufacturable(metaclass=ABCMeta):
    """
    A class that can be initialized asynchronously.
    """

    @classmethod
    @abstractmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """


type Factory[T] = (
    type[Intersection[T, Manufacturable]] | Intersection[type[T], Callable[[], T]]
)


async def new[T](cls: Factory[T], /) -> T:
    """
    Create a new instance of the given class.
    """
    if isinstance(cls, Manufacturable):
        return await cls.new()
    return cls()
