"""
The factory API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Self


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


# @todo Finish this
def new():
    raise NotImplementedError
