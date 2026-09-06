"""
Provide utilities for testing Betty or other software that depends on Betty.
"""

from __future__ import annotations

from typing import final


@final
class AbstractMethod(NotImplementedError):
    """
    Raised by abstract methods.

    This is used in tests, where :py:class:`abc.ABCMeta` cannot be used.
    """

    def __init__(self):
        super().__init__(  # pragma: no cover
            "This is an abstract method and must be overridden by a subclass."
        )


@final
class Counter:
    """
    An object that keeps track of how often it has been called.
    """

    def __init__(self):
        self.count = 0
        """
        The call count.
        """

    def __call__(self) -> int:
        """
        Increment the counter.
        """
        self.count += 1
        return self.count
