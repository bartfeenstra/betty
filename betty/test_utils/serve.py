"""
Test utilities for :py:mod:`betty.serve`.
"""

from typing import Any

from typing_extensions import override

from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.serve import ProjectServer, Server


class NoOpServer(Server):
    """
    A server that does nothing.
    """

    def __init__(self, *_: Any, **__: Any):
        Server.__init__(self, DEFAULT_LOCALIZER)

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


class NoOpProjectServer(NoOpServer, ProjectServer):
    """
    A project server that does nothing.
    """
