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
