"""
The frozen API.

This API provides tools to build cooperative and conditional (im)mutability.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import Enum
from pathlib import Path
from types import NoneType
from typing import Any, final

from babel import Locale
from typing_extensions import sentinel

from betty.importlib import fully_qualified_name


class FrozenError(Exception):
    """
    Raised for frozen API errors.
    """


class NotFreezable(ValueError, FrozenError):
    """
    Raise when a value is not freezable.
    """

    def __init__(self, value: Any, /):
        super().__init__(
            f"{fully_qualified_name(value)} is not freezable. It must be one of {', '.join(map(fully_qualified_name, _frozen_types))}, or subclass {fully_qualified_name(Freezable)}."
        )


class NotYetFrozen(ValueError, FrozenError):
    """
    Raised when a value is not (yet) frozen.
    """

    def __init__(self, value: Frosty, /):
        super().__init__(f"{value} is not (yet) frozen.")


class FrozenAlready(ValueError, FrozenError):
    """
    Raised when a value is frozen already.
    """

    def __init__(self, value: Frosty, /):
        super().__init__(f"{value} is frozen.")


_frozen_types: tuple[type, ...] = ()


def frozen[T](frozen_type: type[T], *frozen_types: type) -> type[T]:
    """
    Mark classes as frozen (immutable).
    """
    global _frozen_types
    _frozen_types = _frozen_types + (frozen_type,) + frozen_types
    return frozen_type


# Python types.
frozen(
    bool,
    Enum,
    float,
    frozenset,
    int,
    NoneType,
    Path,
    sentinel,
    str,
    tuple,
    type,
)

# Vendor types.
frozen(
    Locale,
)


def is_frozen(value: Any) -> bool:
    """
    Check if a value is frozen (immutable) and must not be changed.
    """
    if isinstance(value, _frozen_types):
        return True
    return isinstance(value, Frosty) and value.is_frozen


def freeze[T](value: T) -> T:
    """
    Freeze a value, if possible.
    """
    if isinstance(value, Freezable):
        value.freeze()
        return value
    if is_frozen(value):
        return value
    raise NotFreezable(value)


class Freezer:
    """
    An object that could make itself frozen (immutable).
    """

    __slots__ = ()

    def _freeze(self) -> None:
        """
        Ensure that the object is frozen (immutable).
        """
        return


class Frosty(Freezer, metaclass=ABCMeta):
    """
    An object that may be in a frozen (immutable) state.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def is_frozen(self) -> bool:
        """
        Whether the object is currently frozen.
        """

    @final
    def assert_frozen(self) -> None:
        """
        Assert that the object is currently frozen.
        """
        if not self.is_frozen:
            raise NotYetFrozen(self)

    @final
    def assert_not_frozen(self) -> None:
        """
        Assert that the object is currently not frozen.
        """
        if self.is_frozen:
            raise FrozenAlready(self)


class Freezable(Frosty):
    """
    An object that can be frozen (made immutable) by external code.
    """

    __slots__ = ()

    @final
    def freeze(self) -> None:
        """
        Ensure that the object is frozen (immutable).
        """
        self._freeze()


class FreezableClassVar[OwnerT](metaclass=ABCMeta):
    """
    A freezable class variable.
    """

    @abstractmethod
    def freeze(self, owner: OwnerT, /) -> None:
        """
        Freeze the class var for the given owner.
        """
