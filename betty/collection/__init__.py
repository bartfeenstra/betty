"""
Collection data tpes.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection


class MutableCollection[ValueT](Collection[ValueT]):
    """
    A mutable collection of values.
    """

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all values from the collection.
        """
