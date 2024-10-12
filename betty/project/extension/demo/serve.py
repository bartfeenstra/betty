"""
Tools to serve demonstration sites.
"""

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import final, TYPE_CHECKING

from typing_extensions import override

from betty import serve
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import load, generate
from betty.project.extension.demo.project import create_project
from betty.serve import Server, NoPublicUrlBecauseServerNotStartedError

if TYPE_CHECKING:
    from betty.app import App


@final
class DemoServer(Server):
    """
    Serve the Betty demonstration site.
    """

    def __init__(
        self,
        app: App,
    ):
        super().__init__(localizer=DEFAULT_LOCALIZER)
        self._app = app
        self._server: Server | None = None
        self._exit_stack = AsyncExitStack()

    @override
    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise NoPublicUrlBecauseServerNotStartedError()

    @override
    async def start(self) -> None:
        try:
            project = await self._exit_stack.enter_async_context(
                create_project(self._app)
            )
            self._localizer = await self._app.localizer
            await load.load(project)
            self._server = await serve.BuiltinProjectServer.new_for_project(project)
            await self._exit_stack.enter_async_context(self._server)
            project.configuration.url = self._server.public_url
            await generate.generate(project)
        except BaseException:
            await self.stop()
            raise

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()
