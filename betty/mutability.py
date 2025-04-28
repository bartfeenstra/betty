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

    def get_mutable_instances(self) -> Iterable[Mutable]:
        """
        Get any other :py:class:`betty.mutability.Mutable` instances contained by this one.
        """
        return ()

    @property
    def is_mutable(self) -> bool:
        """
        Whether the instance is mutable.
        """
        return self._mutable

    def mutable(self) -> None:
        """
        Mark the instance mutable.
        """
        self._mutable = True
        for instance in self.get_mutable_instances():
            instance.mutable()

    @property
    def is_immutable(self) -> bool:
        """
        Whether the instance is immutable.
        """
        return not self._mutable

    def immutable(self) -> None:
        """
        Mark the instance immutable.
        """
        self._mutable = False
        for instance in self.get_mutable_instances():
            instance.immutable()

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


def mutable(*instances: Mutable) -> None:
    """
    Mark the given instances mutable.
    """
    for instance in instances:
        instance.mutable()


def immutable(*instances: Mutable) -> None:
    """
    Mark the given instances immutable.
    """
    for instance in instances:
        instance.immutable()
