"""
Servers that do nothing.
"""

from __future__ import annotations

from typing import Any, final, override

from betty.server import Server
from betty.test_utils.user import StaticUser


@final
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
