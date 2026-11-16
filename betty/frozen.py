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

from betty.classtools.class_var import ClassVar, ClassVars
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

    def __init__(self, value: Freezable, /):
        super().__init__(f"{value} is not (yet) frozen.")


class FrozenAlready(ValueError, FrozenError):
    """
    Raised when a value is frozen already.
    """

    def __init__(self, value: Freezable, /):
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
    return isinstance(value, Freezable) and value.is_frozen


def freeze[T](value: T) -> None:
    """
    Freeze a value, if possible.
    """
    if isinstance(value, Freezable):
        value.freeze()
    if is_frozen(value):
        return
    raise NotFreezable(value)


class Freezable(metaclass=ABCMeta):
    """
    An object that may be in a frozen (immutable) state.
    """

    __slots__ = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._freezable_class_vars = ClassVars(cls, FreezableClassVar)

    def freeze(self) -> None:
        """
        Ensure that the object is frozen (immutable).
        """
        if self.is_frozen:
            return
        for class_var in self._freezable_class_vars:
            class_var.freeze(self)

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


class FreezableClassVar[OwnerT](ClassVar[OwnerT], metaclass=ABCMeta):
    """
    A freezable class variable.
    """

    @abstractmethod
    def freeze(self, owner: OwnerT, /) -> None:
        """
        Freeze the class var for the given owner.
        """
