"""
The mutability API.

This provides tools to mark objects as mutable or immutable, and to guard against mutations.
"""

from __future__ import annotations

from typing import Any, final


class MutabilityError(Exception):
    """
    A generic mutability API error.
    """


class MutableError(MutabilityError, RuntimeError):
    """
    Raised because something was unexpectedly mutable.
    """


class ImmutableError(MutabilityError, RuntimeError):
    """
    Raised because something was unexpectedly immutable.
    """


class Mutable:
    """
    A generic mutable type that can be marked immutable.
    """

    def __init__(self, *args: Any, mutable: bool = True, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.mutable = mutable
        """
        Whether the instance is mutable.
        """

    @final
    def assert_mutable(self) -> None:
        """
        Assert that the instance is mutable.

        :raise ImmutableError: if the instance is immutable.
        """
        if not self.mutable:
            raise ImmutableError(
                f"{self} was unexpectedly immutable, and cannot be modified."
            )

    @final
    def assert_immutable(self) -> None:
        """
        Assert that the instance is immutable.

        :raise MutableError: if the instance is mutable.
        """
        if self.mutable:
            raise MutableError(f"{self} was unexpectedly mutable, and can be modified.")
