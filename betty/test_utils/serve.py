"""
Test utilities for :py:mod:`betty.serve`.
"""

from typing import Any

from typing_extensions import override

from betty.serve import ProjectServer, Server
from betty.test_utils.user import StaticUser


class NoOpServer(Server):
    """
    A server that does nothing.
    """

    def __init__(self, *_: Any, **__: Any):
        super().__init__(user=StaticUser())

    @override
    @property
    def public_url(self) -> str:
        return "https://example.com"

    @override
    async def start(self) -> None:
        pass

    @override
    async def stop(self) -> None:
        pass

    @override
    async def show(self) -> None:
        pass


class NoOpProjectServer(ProjectServer, NoOpServer):
    """
    A project server that does nothing.
    """
