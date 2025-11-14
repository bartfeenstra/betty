"""
The mutability API.

This provides tools to mark objects as mutable or immutable, and to guard against mutations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Iterable


class MutabilityError(Exception):
    """
    A generic mutability API error.
    """


@internal
class MutableError(MutabilityError, RuntimeError):
    """
    An error raised because something was unexpectedly mutable.
    """


@internal
class ImmutableError(MutabilityError, RuntimeError):
    """
    An error raised because something was unexpectedly immutable.
    """


class Mutable:
    """
    A generic mutable type that can be marked immutable.
    """

    def __init__(self, *args: Any, mutable: bool = True, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._mutable = mutable

    def get_mutables(self) -> Iterable[object]:
        """
        Get any other objects contained by this one that may also be :py:class:`betty.mutability.Mutable`.
        """
        return ()

    def _propagate_mutability(self) -> None:
        function = mutable if self.mutable else immutable
        function(*self.get_mutables())

    @property
    def mutable(self) -> bool:
        """
        Whether the instance is mutable.
        """
        return self._mutable

    @mutable.setter
    def mutable(self, mutable: bool) -> None:
        self._mutable = mutable
        self._propagate_mutability()

    @property
    def immutable(self) -> bool:
        """
        Whether the instance is immutable.
        """
        return not self._mutable

    @immutable.setter
    def immutable(self, immutable: bool) -> None:
        self.mutable = not immutable

    def assert_mutable(self) -> None:
        """
        Assert that the instance is mutable.

        :raise ImmutableError: if the instance is immutable.
        """
        if not self._mutable:
            raise ImmutableError(
                f"{self} was unexpectedly immutable, and cannot be modified."
            )

    def assert_immutable(self) -> None:
        """
        Assert that the instance is immutable.

        :raise MutableError: if the instance is mutable.
        """
        if self._mutable:
            raise MutableError(f"{self} was unexpectedly mutable, and can be modified.")


def mutable(*instances: Any) -> None:
    """
    Mark the given instances mutable.
    """
    for instance in instances:
        if isinstance(instance, Mutable):
            instance.mutable = True


def immutable(*instances: Any) -> None:
    """
    Mark the given instances immutable.
    """
    for instance in instances:
        if isinstance(instance, Mutable):
            instance.immutable = True
