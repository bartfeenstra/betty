"""
Reusable collections.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable

type KeyResolver[KeyT, ResolvableKeyT] = Callable[[KeyT | ResolvableKeyT], KeyT]
type ValueResolver[ValueT, ResolvableValueT] = Callable[
    [ValueT | ResolvableValueT], ValueT
]


class KeyResolvable[KeyT, ResolvableKeyT](metaclass=ABCMeta):
    """
    A collection that can resolve a wide range of data to its internal key type.
    """

    __slots__ = ()

    @abstractmethod
    def resolve_key(self, key: KeyT | ResolvableKeyT, /) -> KeyT:
        """
        Resolve a key.
        """


class ValueResolvable[ValueT, ResolvableValueT](metaclass=ABCMeta):
    """
    A collection that can resolve a wide range of data to its internal value type.
    """

    __slots__ = ()

    @abstractmethod
    def resolve_value(self, value: ValueT | ResolvableValueT, /) -> ValueT:
        """
        Resolve a value.
        """
