"""
Progress tracking that does nothing.
"""

from typing_extensions import override

from betty.progress import Progress


class NoOpProgress(Progress):
    """
    A progress tracker that does nothing.
    """

    @override
    async def add(self, add: int = 1) -> None:
        pass

    @override
    async def done(self, done: int = 1) -> None:
        pass
