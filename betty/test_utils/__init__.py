"""
Provide utilities for testing Betty or other software that depends on Betty.
"""

from typing import final


@final
class Counter:
    """
    An object that keeps track of how often it has been called.
    """

    def __init__(self):
        self._count = 0

    @property
    def count(self) -> int:
        """
        The call count.
        """
        return self._count

    def __call__(self) -> int:
        """
        Increment the counter.
        """
        self._count += 1
        return self._count
