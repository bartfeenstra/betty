"""
Documentation servers.
"""

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, final, override

from betty.documentation import _ensure_www_directory
from betty.pathlib import StrPath, resolve_path
from betty.server import Server, ServerNotStarted
from betty.servers import builtin

if TYPE_CHECKING:
    from betty.user import User


@final
class DocumentationServer(Server):
    """
    Serve the documentation site.
    """

    def __init__(self, cache_directory: StrPath, *, user: User):
        super().__init__(user=user)
        self._cache_directory = resolve_path(cache_directory)
        self._server: Server | None = None
        self._exit_stack = AsyncExitStack()

    @override
    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise ServerNotStarted

    @override
    async def start(self) -> None:
        www_directory = self._cache_directory / "www"
        await _ensure_www_directory(
            www_directory, self._cache_directory / "cache", user=self._user
        )
        self._server = builtin.BuiltinServer(www_directory, user=self._user)
        await self._exit_stack.enter_async_context(self._server)

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()
