"""
Task progress management.
"""

from abc import ABC, abstractmethod


class Progress(ABC):
    """
    Track the progress of a number of tasks.
    """

    @abstractmethod
    async def add(self, add: int = 1) -> None:
        """
        Add a number of tasks to the total.
        """

    @abstractmethod
    async def done(self, done: int = 1) -> None:
        """
        Mark a number of tasks done.
        """
